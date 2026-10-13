# Google Cloud Run Enterprise Deployment
# Autoscaling, VPC egress, and least-privilege service account bindings

resource "google_cloud_run_v2_service" "workflow_mining_service" {
  name     = "workflow-mining-agent"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    service_account = google_service_account.app_runner_sa.email

    containers {
      image = var.container_image

      resources {
        limits = {
          cpu    = "4"
          memory = "8Gi"
        }
        cpu_idle = false
      }

      env {
        name  = "APP_MODE"
        value = "GCP"
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "BIGQUERY_DATASET"
        value = google_bigquery_dataset.workflow_mining_dataset.dataset_id
      }
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      ports {
        container_port = 8000
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        initial_delay_seconds = 5
        period_seconds        = 10
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        period_seconds    = 15
        failure_threshold = 3
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_project_service.required_apis,
    google_service_account.app_runner_sa
  ]
}

# Public Ingress Policy (or restrict to corporate IAP)
resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.workflow_mining_service.location
  service  = google_cloud_run_v2_service.workflow_mining_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
