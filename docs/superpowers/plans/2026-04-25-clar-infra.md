# CLAR Infrastructure & CI/CD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy CLAR to GCP Cloud Run using Terraform, wire up GitHub Actions CI/CD with Workload Identity Federation (no long-lived keys), and verify the live URL with a smoke test.

**Architecture:** A 3-stage Docker build packages the Next.js static export and FastAPI backend into a single `linux/amd64` image. Terraform provisions Cloud Run, Artifact Registry, and Secret Manager — adapted from the cyber project. GitHub Actions `ci.yml` runs lint + tests + docker build on every PR; `cd.yml` builds, pushes, deploys, and smoke-tests on merge to main. Workload Identity Federation authenticates GitHub Actions to GCP — no service account JSON keys stored in GitHub Secrets.

**Tech Stack:** Terraform · GCP Cloud Run v2 · GCP Artifact Registry · GCP Secret Manager · GCP Workload Identity Federation · GitHub Actions · Docker multi-stage (linux/amd64)

**Prerequisites:**
- Backend plan complete (passing tests, `requirements.txt` committed)
- Frontend plan complete (static export building cleanly)
- GCP project exists (reuse from cyber project)
- `gcloud` CLI installed and authenticated locally
- `terraform` CLI installed locally

---

## File Map

```
clar/
  infra/
    terraform/
      main.tf            # All GCP resources
      variables.tf       # Project ID, region, image tag
      outputs.tf         # service_url, registry_url
      terraform.tfvars   # Local values — NOT committed (in .gitignore)
  infra/docker/
    Dockerfile           # 3-stage build (node → python builder → runtime)
    docker-compose.yml   # (already exists from backend plan)
  .github/
    workflows/
      ci.yml             # Lint + test + docker build (every PR)
      cd.yml             # Build + push + deploy + smoke test (merge to main)
  .gitignore             # Add terraform.tfvars, .terraform/
```

---

## Task 1: Update Dockerfile — 3-Stage Build (Node + Python + Runtime)

**Files:**
- Modify: `infra/docker/Dockerfile`

The backend plan created a 2-stage Python-only Dockerfile. This task adds a Node stage to bake the Next.js static export into the image.

- [ ] **Step 1: Replace `infra/docker/Dockerfile` with the 3-stage version**

```dockerfile
# syntax=docker/dockerfile:1
# Stage 1: Build Next.js static export
FROM node:20-alpine AS node-builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is passed as a build arg
ARG NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
ENV NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=$NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
ARG NEXT_PUBLIC_API_URL=/
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

# Stage 2: Install Python deps
FROM python:3.11-slim AS python-builder
RUN pip install uv
WORKDIR /build
COPY requirements.txt .
RUN uv pip install --target /venv -r requirements.txt
RUN python -m spacy download en_core_web_lg --target /venv

# Stage 3: Runtime (non-root)
FROM python:3.11-slim
COPY --from=python-builder /venv /venv
ENV PYTHONPATH=/venv
WORKDIR /app
COPY app/ app/
COPY --from=node-builder /frontend/out ./static
RUN useradd -m clar && chown -R clar /app
USER clar
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Test the 3-stage build locally**

```bash
docker build \
  --platform linux/amd64 \
  --build-arg NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_placeholder \
  -f infra/docker/Dockerfile \
  -t clar:local .
```

Expected: Build completes successfully. No errors.

- [ ] **Step 3: Run the built image**

```bash
docker run --rm -p 8000:8000 \
  --env-file .env \
  clar:local &
sleep 5
curl http://localhost:8000/health
# Expected: {"status":"ok","version":"1.0.0"}
curl http://localhost:8000/ | head -20
# Expected: HTML — the Next.js static export
docker stop $(docker ps -q --filter ancestor=clar:local)
```

- [ ] **Step 4: Commit**

```bash
git add infra/docker/Dockerfile
git commit -m "feat: Dockerfile — 3-stage build (Node + Python + runtime), linux/amd64"
```

---

## Task 2: Terraform — GCP Resources

**Files:**
- Create: `infra/terraform/variables.tf`
- Create: `infra/terraform/main.tf`
- Create: `infra/terraform/outputs.tf`
- Modify: `.gitignore`

- [ ] **Step 1: Add terraform entries to `.gitignore`**

If `.gitignore` doesn't exist, create it. Add these lines:

```
# Terraform
infra/terraform/.terraform/
infra/terraform/.terraform.lock.hcl
infra/terraform/terraform.tfvars
infra/terraform/terraform.tfstate
infra/terraform/terraform.tfstate.backup

# Environment
.env
```

- [ ] **Step 2: Create `infra/terraform/variables.tf`**

```hcl
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

variable "anthropic_api_key" {
  description = "Anthropic API key — stored in Secret Manager"
  type        = string
  sensitive   = true
}

variable "langsmith_api_key" {
  description = "LangSmith API key — stored in Secret Manager"
  type        = string
  sensitive   = true
}
```

- [ ] **Step 3: Create `infra/terraform/main.tf`**

```hcl
terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  registry_host = "${var.region}-docker.pkg.dev"
  image_name    = "${local.registry_host}/${var.project_id}/clar/clar:${var.image_tag}"
}

# Enable required APIs
resource "google_project_service" "cloud_run" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifact_registry" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "secret_manager" {
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

# Artifact Registry repository
resource "google_artifact_registry_repository" "clar" {
  location      = var.region
  repository_id = "clar"
  format        = "DOCKER"
  depends_on    = [google_project_service.artifact_registry]
}

# Secret Manager — ANTHROPIC_API_KEY
resource "google_secret_manager_secret" "anthropic_api_key" {
  secret_id  = "ANTHROPIC_API_KEY"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret_version" "anthropic_api_key" {
  secret      = google_secret_manager_secret.anthropic_api_key.id
  secret_data = var.anthropic_api_key
}

# Secret Manager — LANGSMITH_API_KEY
resource "google_secret_manager_secret" "langsmith_api_key" {
  secret_id  = "LANGSMITH_API_KEY"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret_version" "langsmith_api_key" {
  secret      = google_secret_manager_secret.langsmith_api_key.id
  secret_data = var.langsmith_api_key
}

# Cloud Run service
resource "google_cloud_run_v2_service" "clar" {
  name     = "clar"
  location = var.region

  template {
    scaling {
      min_instance_count = 1  # keep warm during demo; set to 0 after submission
      max_instance_count = 10
    }
    containers {
      image = local.image_name

      resources {
        limits = {
          cpu    = "1"
          memory = "2Gi"
        }
      }

      env {
        name = "ANTHROPIC_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.anthropic_api_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "LANGSMITH_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.langsmith_api_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "ENVIRONMENT"
        value = "production"
      }

      env {
        name  = "LANGSMITH_PROJECT"
        value = "clar-production"
      }

      ports {
        container_port = 8000
      }

      liveness_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 10
        period_seconds        = 30
      }
    }
  }

  depends_on = [
    google_project_service.cloud_run,
    google_artifact_registry_repository.clar,
    google_secret_manager_secret_version.anthropic_api_key,
    google_secret_manager_secret_version.langsmith_api_key,
  ]
}

# Make Cloud Run service publicly accessible
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.clar.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Grant Cloud Run service account access to secrets
resource "google_secret_manager_secret_iam_member" "anthropic_access" {
  secret_id = google_secret_manager_secret.anthropic_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_cloud_run_v2_service.clar.template[0].service_account == "" ? "${data.google_project.project.number}-compute@developer.gserviceaccount.com" : google_cloud_run_v2_service.clar.template[0].service_account}"
}

resource "google_secret_manager_secret_iam_member" "langsmith_access" {
  secret_id = google_secret_manager_secret.langsmith_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

data "google_project" "project" {
  project_id = var.project_id
}
```

- [ ] **Step 4: Create `infra/terraform/outputs.tf`**

```hcl
output "service_url" {
  description = "CLAR Cloud Run service URL"
  value       = google_cloud_run_v2_service.clar.uri
}

output "registry_url" {
  description = "Artifact Registry URL for Docker images"
  value       = "${local.registry_host}/${var.project_id}/clar"
}
```

- [ ] **Step 5: Create `infra/terraform/terraform.tfvars` (local only — never commit)**

```hcl
project_id        = "your-gcp-project-id"
region            = "us-central1"
anthropic_api_key = "sk-ant-..."
langsmith_api_key = "ls__..."
```

Verify it's in `.gitignore`:
```bash
git check-ignore infra/terraform/terraform.tfvars
# Expected: infra/terraform/terraform.tfvars
```

- [ ] **Step 6: Init and validate Terraform**

```bash
cd infra/terraform
terraform init
terraform validate
```

Expected: `Success! The configuration is valid.`

- [ ] **Step 7: Commit Terraform files (not tfvars)**

```bash
cd ../..
git add infra/terraform/main.tf infra/terraform/variables.tf infra/terraform/outputs.tf
git add .gitignore
git commit -m "feat: Terraform — Cloud Run, Artifact Registry, Secret Manager (GCP)"
```

---

## Task 3: Workload Identity Federation Setup (one-time manual step)

This sets up GitHub Actions → GCP authentication without any long-lived service account keys. Run these commands locally with `gcloud` once.

- [ ] **Step 1: Set environment variables**

```bash
export PROJECT_ID="your-gcp-project-id"
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
export REPO="your-github-username/clar"  # e.g. stellaacharoiro/clar
```

- [ ] **Step 2: Enable IAM Credentials API**

```bash
gcloud services enable iamcredentials.googleapis.com --project=$PROJECT_ID
```

- [ ] **Step 3: Create a Workload Identity Pool**

```bash
gcloud iam workload-identity-pools create "github-pool" \
  --project=$PROJECT_ID \
  --location="global" \
  --display-name="GitHub Actions Pool"
```

- [ ] **Step 4: Create a Workload Identity Provider**

```bash
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project=$PROJECT_ID \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Actions Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

- [ ] **Step 5: Create a service account for GitHub Actions**

```bash
gcloud iam service-accounts create "github-actions-sa" \
  --project=$PROJECT_ID \
  --display-name="GitHub Actions SA"
```

- [ ] **Step 6: Grant the service account the roles it needs**

```bash
# Push to Artifact Registry
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Deploy to Cloud Run
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.developer"

# Act as the Cloud Run runtime service account
gcloud iam service-accounts add-iam-policy-binding \
  "${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --project=$PROJECT_ID \
  --role="roles/iam.serviceAccountUser" \
  --member="serviceAccount:github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com"
```

- [ ] **Step 7: Bind Workload Identity Pool to the service account**

```bash
gcloud iam service-accounts add-iam-policy-binding \
  "github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project=$PROJECT_ID \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/attribute.repository/${REPO}"
```

- [ ] **Step 8: Note the Workload Identity Provider resource name**

```bash
gcloud iam workload-identity-pools providers describe "github-provider" \
  --project=$PROJECT_ID \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --format="value(name)"
```

Copy the output. It looks like:
`projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider`

This goes into GitHub Secrets as `GCP_WORKLOAD_IDENTITY_PROVIDER`.

- [ ] **Step 9: Add GitHub Secrets**

Go to: `https://github.com/your-username/clar/settings/secrets/actions`

Add these secrets:
| Secret name | Value |
|---|---|
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | The provider resource name from step 8 |
| `GCP_SERVICE_ACCOUNT` | `github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com` |
| `GCP_PROJECT_ID` | Your GCP project ID |
| `GCP_REGION` | `us-central1` |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Your Clerk publishable key (baked into Docker build) |

---

## Task 4: GitHub Actions — `ci.yml`

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install Python dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt

      - name: Download spaCy model
        run: python -m spacy download en_core_web_lg

      - name: Ruff lint
        run: ruff check app/ tests/

      - name: Mypy type check
        run: mypy app/

      - name: Pytest (>80% coverage required)
        run: pytest tests/unit/ tests/integration/ -v --cov=app --cov-report=xml --cov-fail-under=80
        env:
          ANTHROPIC_API_KEY: "sk-ant-test-key"
          LANGSMITH_API_KEY: "test"
          LANGSMITH_PROJECT: "clar-ci"
          CLERK_JWKS_URL: "https://example.clerk.accounts.dev/.well-known/jwks.json"
          ENVIRONMENT: "test"

      - name: Upload coverage report
        uses: codecov/codecov-action@v4
        if: always()
        with:
          files: coverage.xml

      - name: Set up Node.js 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: frontend/package-lock.json

      - name: Install Node dependencies
        working-directory: frontend
        run: npm ci

      - name: Next.js build (static export)
        working-directory: frontend
        run: npm run build
        env:
          NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: "pk_test_placeholder"
          NEXT_PUBLIC_API_URL: "/"

      - name: Docker build smoke test (no push)
        run: |
          docker build \
            --platform linux/amd64 \
            --build-arg NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_placeholder \
            -f infra/docker/Dockerfile \
            -t clar:ci-test .
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "feat: GitHub Actions ci.yml — lint, test, coverage, docker build (every PR)"
```

---

## Task 5: GitHub Actions — `cd.yml`

**Files:**
- Create: `.github/workflows/cd.yml`

- [ ] **Step 1: Create `.github/workflows/cd.yml`**

```yaml
name: CD

on:
  push:
    branches: [main]

permissions:
  contents: read
  id-token: write  # Required for Workload Identity Federation

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      # ---------- CI steps (repeat on main) ----------

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install Python dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt

      - name: Download spaCy model
        run: python -m spacy download en_core_web_lg

      - name: Ruff + Mypy
        run: |
          ruff check app/ tests/
          mypy app/

      - name: Pytest
        run: pytest tests/unit/ tests/integration/ -v --cov=app --cov-fail-under=80
        env:
          ANTHROPIC_API_KEY: "sk-ant-test-key"
          LANGSMITH_API_KEY: "test"
          LANGSMITH_PROJECT: "clar-ci"
          CLERK_JWKS_URL: "https://example.clerk.accounts.dev/.well-known/jwks.json"
          ENVIRONMENT: "test"

      # ---------- GCP auth ----------

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}

      - name: Set up gcloud CLI
        uses: google-github-actions/setup-gcloud@v2

      - name: Configure Docker for Artifact Registry
        run: gcloud auth configure-docker ${{ secrets.GCP_REGION }}-docker.pkg.dev --quiet

      # ---------- Build + push ----------

      - name: Set image tag
        run: echo "IMAGE_TAG=${{ secrets.GCP_REGION }}-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/clar/clar:${{ github.sha }}" >> $GITHUB_ENV

      - name: Build + push Docker image
        run: |
          docker build \
            --platform linux/amd64 \
            --build-arg NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=${{ secrets.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY }} \
            --build-arg NEXT_PUBLIC_API_URL=/ \
            -f infra/docker/Dockerfile \
            -t ${{ env.IMAGE_TAG }} .
          docker push ${{ env.IMAGE_TAG }}

      # ---------- Deploy ----------

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy clar \
            --image ${{ env.IMAGE_TAG }} \
            --platform managed \
            --region ${{ secrets.GCP_REGION }} \
            --project ${{ secrets.GCP_PROJECT_ID }} \
            --quiet

      - name: Get service URL
        id: get_url
        run: |
          SERVICE_URL=$(gcloud run services describe clar \
            --platform managed \
            --region ${{ secrets.GCP_REGION }} \
            --project ${{ secrets.GCP_PROJECT_ID }} \
            --format "value(status.url)")
          echo "SERVICE_URL=$SERVICE_URL" >> $GITHUB_ENV

      - name: Smoke test
        run: |
          sleep 5
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${{ env.SERVICE_URL }}/health)
          if [ "$STATUS" != "200" ]; then
            echo "Smoke test FAILED — /health returned $STATUS"
            exit 1
          fi
          echo "Smoke test PASSED — ${{ env.SERVICE_URL }}/health returned 200"

      - name: Write deployment summary
        if: always()
        run: |
          echo "## Deployment Summary" >> $GITHUB_STEP_SUMMARY
          echo "- **Image:** \`${{ env.IMAGE_TAG }}\`" >> $GITHUB_STEP_SUMMARY
          echo "- **Service URL:** ${{ env.SERVICE_URL }}" >> $GITHUB_STEP_SUMMARY
          echo "- **Smoke test:** ${{ job.status }}" >> $GITHUB_STEP_SUMMARY
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/cd.yml
git commit -m "feat: GitHub Actions cd.yml — build, push, deploy, smoke test (merge to main)"
```

---

## Task 6: First Production Deployment

- [ ] **Step 1: Push to GitHub and open a PR**

```bash
git push origin main
```

If you're working on a branch:
```bash
git push origin your-branch
# Then open a PR to main on GitHub
```

Expected: CI workflow triggers. All steps pass.

- [ ] **Step 2: Merge PR to main**

Expected: CD workflow triggers automatically.

Watch the Actions tab. Verify:
1. All CI steps pass (lint, test, coverage, docker build)
2. GCP auth succeeds (Workload Identity)
3. Docker image pushes to Artifact Registry
4. `gcloud run deploy` completes
5. Smoke test returns 200

- [ ] **Step 3: Run Terraform for first-time infrastructure setup**

If Cloud Run service, Artifact Registry, and Secret Manager don't exist yet in GCP:

```bash
cd infra/terraform
terraform plan -out=tfplan
# Review the plan — confirm you see: Cloud Run service, Artifact Registry repo, 2 secrets
terraform apply tfplan
```

Expected: All resources created. `terraform output` shows `service_url` and `registry_url`.

Note: After the first `terraform apply`, subsequent deploys use `gcloud run deploy` (in `cd.yml`), not Terraform. Terraform manages infrastructure; the pipeline manages image updates.

- [ ] **Step 4: Verify live deployment**

```bash
SERVICE_URL=$(cd infra/terraform && terraform output -raw service_url)
curl $SERVICE_URL/health
# Expected: {"status":"ok","version":"1.0.0"}
curl $SERVICE_URL/metrics | grep clar_
# Expected: Prometheus metrics with clar_ prefix
```

Open `$SERVICE_URL` in a browser — CLAR upload screen loads.

- [ ] **Step 5: Test full upload flow on production**

```bash
curl -X POST $SERVICE_URL/api/upload \
  -F "file=@tests/fixtures/sample_cbc.txt" | python3 -m json.tool
```

Expected: JSON response with `report_id`, `findings`, `questions`.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "chore: infra complete — terraform, CI/CD, first production deployment verified"
```

---

## Task 7: Post-Submission Cleanup (after demo)

This task is run AFTER submission to avoid unnecessary GCP costs.

- [ ] **Step 1: Scale Cloud Run to zero**

Edit `infra/terraform/main.tf` — change `min_instance_count` from `1` to `0`:

```hcl
scaling {
  min_instance_count = 0  # changed from 1 after submission
  max_instance_count = 10
}
```

```bash
cd infra/terraform
terraform apply -auto-approve
```

Expected: Cloud Run scales to zero when idle. Cold starts will occur but cost drops to near zero.

- [ ] **Step 2: Commit**

```bash
cd ../..
git add infra/terraform/main.tf
git commit -m "chore: scale Cloud Run to minScale=0 after submission"
```
