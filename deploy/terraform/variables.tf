variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
  default     = "workflow-mining-enterprise-prod"
}

variable "region" {
  description = "Primary GCP Region for deployment"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Target deployment environment"
  type        = string
  default     = "production"
}

variable "container_image" {
  description = "Container image tag in Google Artifact Registry"
  type        = string
  default     = "us-central1-docker.pkg.dev/workflow-mining-enterprise-prod/apps/workflow-mining-agent:v1.0.0"
}

variable "min_instances" {
  description = "Minimum warm instances for Cloud Run autoscaling"
  type        = number
  default     = 1
}

variable "max_instances" {
  description = "Maximum instances for Cloud Run autoscaling"
  type        = number
  default     = 20
}

variable "retention_days" {
  description = "BigQuery ticket table partition retention period in days"
  type        = number
  default     = 90
}
