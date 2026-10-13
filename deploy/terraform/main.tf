terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.30.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Enable Required Google Cloud Enterprise APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "bigquery.googleapis.com",
    "aiplatform.googleapis.com",
    "dlp.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudkms.googleapis.com",
    "cloudtasks.googleapis.com",
    "artifactregistry.googleapis.com",
    "compute.googleapis.com"
  ])
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# 2. Artifact Registry for Container Storage
resource "google_artifact_registry_repository" "app_repo" {
  location      = var.region
  repository_id = "apps"
  description   = "Docker repository for Workflow Mining Agent SaaS container images"
  format        = "DOCKER"
  depends_on    = [google_project_service.required_apis]
}
