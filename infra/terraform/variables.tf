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
