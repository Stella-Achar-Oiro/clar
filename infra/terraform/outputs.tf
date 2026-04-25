output "service_url" {
  description = "CLAR Cloud Run service URL"
  value       = google_cloud_run_v2_service.clar.uri
}

output "registry_url" {
  description = "Artifact Registry URL for Docker images"
  value       = "${local.registry_host}/${var.project_id}/clar"
}
