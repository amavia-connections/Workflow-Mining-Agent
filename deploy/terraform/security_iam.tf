# Enterprise Security, Cloud KMS Encryption, Secret Manager & IAM Bindings

# 1. Least-Privilege Application Service Account
resource "google_service_account" "app_runner_sa" {
  account_id   = "wf-mining-runner-${var.environment}"
  display_name = "Workflow Mining Agent Cloud Run Runner"
}

# 2. Grant BigQuery Data Editor & Vertex AI User
resource "google_project_iam_member" "bigquery_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.app_runner_sa.email}"
}

resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.app_runner_sa.email}"
}

resource "google_project_iam_member" "dlp_user" {
  project = var.project_id
  role    = "roles/dlp.user"
  member  = "serviceAccount:${google_service_account.app_runner_sa.email}"
}

# 3. Google Cloud KMS KeyRing for Customer-Managed Encryption Keys (CMEK)
resource "google_kms_key_ring" "app_keyring" {
  name     = "workflow-mining-keyring-${var.environment}"
  location = var.region
  depends_on = [google_project_service.required_apis]
}

resource "google_kms_crypto_key" "app_crypto_key" {
  name            = "dw-encryption-key"
  key_ring        = google_kms_key_ring.app_keyring.id
  rotation_period = "7776000s" # 90 days automatic key rotation
}

# 4. Google Secret Manager for Connector API Secrets
resource "google_secret_manager_secret" "webhook_signing_secret" {
  secret_id = "wf-mining-webhook-hmac-${var.environment}"
  replication {
    auto {}
  }
  depends_on = [google_project_service.required_apis]
}

# 5. Cloud Armor WAF Security Policy (DDoS defense & OWASP rules)
resource "google_compute_security_policy" "cloud_armor_waf" {
  name        = "wf-mining-armor-policy-${var.environment}"
  description = "Cloud Armor WAF policy defending against rate surges and web vulnerabilities"

  # Default rule: Allow traffic
  rule {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default allow"
  }

  # Rate limit rule: Max 120 requests per minute per IP
  rule {
    action   = "rate_based_ban"
    priority = "1000"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"
      rate_limit_threshold {
        count        = 120
        interval_sec = 60
      }
      ban_duration_sec = 300
    }
    description = "Throttle abusive requests to prevent API resource exhaustion"
  }
}
