output "cloud_run_service_url" {
  description = "The publicly accessible HTTPS URL of the deployed Workflow Mining Agent service"
  value       = google_cloud_run_v2_service.workflow_mining_service.uri
}

output "bigquery_dataset_id" {
  description = "The provisioned BigQuery data warehouse dataset ID"
  value       = google_bigquery_dataset.workflow_mining_dataset.dataset_id
}

output "artifact_registry_repo" {
  description = "Artifact Registry Docker repository path"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app_repo.name}"
}

output "kms_crypto_key_id" {
  description = "Cloud KMS CMEK key resource identifier"
  value       = google_kms_crypto_key.app_crypto_key.id
}
