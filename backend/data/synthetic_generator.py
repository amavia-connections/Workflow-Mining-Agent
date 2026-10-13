"""
Synthetic IT Service Ticket Generator for Workflow Mining Agent.
AI Builder Cup 2026 - Stage B.

Generates realistic IT service tickets with 6 planted repetitive workflows and noisy one-offs.
Deterministic via random seed.
Ground-truth fields are strictly marked and isolated for Stage F evaluation only.
"""

import random
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple


PLANTED_WORKFLOWS = {
    "WF_ACCESS_PROVISIONING": {
        "name": "Access Provisioning and Permission Requests",
        "description": "Granting IAM roles, folder permissions, repository access, or database credentials upon request.",
        "category": "Identity & Access",
        "typical_handling_range": (15, 30),  # minutes
        "templates": [
            ("Grant {role} access to {resource} for {user}",
             "User {user} requires {role} permissions on {resource} for upcoming project sprint. Manager approval attached.",
             "Verified manager sign-off via ticketing system. Added {user} to group {group} and bound {role} to {resource}. Verified permissions using policy analyzer. Notified user."),
            ("Permission escalation request: {resource}",
             "I cannot access {resource} with error HTTP 403 Forbidden. Need read/write access to deploy configs.",
             "Checked current IAM bindings. Found missing role {role}. Added binding in Cloud Console. User confirmed access restored."),
            ("Add {user} to GitHub repo {repo_name} team",
             "Please add contractor {user} to team {group} with write access to {repo_name}.",
             "Validated contractor security vetting status. Invited {user} to org team with {role} permissions. Sent onboarding guidelines."),
            ("Database read replica access for {user}",
             "Data analyst {user} requests read-only access to BigQuery analytical dataset {resource}.",
             "Generated least-privilege service credential / IAM dataViewer binding. Verified dataset expiration policy. Sent connection string and tested query."),
            ("Access request - {resource} - urgent",
             "Urgent: {user} blocked on client deliverable. Needs temporary elevation to {role} on {resource}.",
             "Obtained emergency change authorization. Granted temporary IAM binding with 24-hour TTL. Logged security audit ticket.")
        ],
        "roles": ["roles/bigquery.dataViewer", "roles/storage.objectAdmin", "roles/container.developer", "DevOps-Contributor", "Data-Analyst-L2"],
        "resources": ["project-analytics-prod", "gs://finance-raw-reports", "k8s-cluster-staging", "bi-reporting-bq", "repo/payment-service"],
        "groups": ["sec-cloud-devs", "fin-analytics-read", "devops-core", "app-engineers"],
        "repos": ["checkout-service", "data-pipeline-v2", "auth-gateway", "frontend-portal"]
    },
    "WF_ENV_RESET": {
        "name": "Development or Test Environment Resets",
        "description": "Restoring staging/test databases from sanitized snapshots, restarting services, and flushing caches.",
        "category": "Infrastructure",
        "typical_handling_range": (25, 45),  # minutes
        "templates": [
            ("Reset staging environment {env_id} for QA cycle",
             "Staging env {env_id} has corrupted test data from automated integration test run. Please restore to baseline clean snapshot.",
             "Drained ingress traffic on {env_id}. Executed backup restore script from master clean snapshot. Flushed Redis cache. Executed seed data migration. Ran smoke test suite: all 18 endpoints passed. Reopened to QA."),
            ("Staging test DB desync in {env_id} - restore requested",
             "Database state in {env_id} is inconsistent. FK constraints failing during checkout test. Need reset.",
             "Terminated active connections to Postgres DB. Restored anonymized schema snapshot v4.2. Restarted backend pods. Verified health check /healthz returned 200 OK."),
            ("Sandbox environment {env_id} cleanup and rebuild",
             "Sprint finished. Please teardown ephemeral resources in {env_id} and redeploy latest master branch.",
             "Triggered Cloud Build pipeline reset-sandbox. Shrunk StatefulSet to 0, purged PVCs, applied Terraform baseline. Deployed commit sha. Validated microservice mesh."),
            ("Flush cache and reseed mock data on {env_id}",
             "Automated tests running out of test customer accounts. Please flush Redis cluster and rerun seeder script.",
             "Connected to bastion host. Ran FLUSHDB on Redis cluster. Executed python seed_accounts.py --count 500. Verified mock data present.")
        ],
        "envs": ["staging-us-central1", "qa-regression-02", "dev-sandbox-blue", "perf-test-cluster", "uat-staging-01"]
    },
    "WF_LOG_DISK_CLEANUP": {
        "name": "Log Cleanup and Disk Space Remediation",
        "description": "Purging uncompressed log files, clearing /tmp directories, and rotating logs when disk alarms trigger.",
        "category": "Operations",
        "typical_handling_range": (15, 25),  # minutes
        "templates": [
            ("High Disk Space Alert: {host} filesystem at {pct}%",
             "Monitoring alert P2: Partition /var/log on VM {host} has reached {pct}% capacity. Immediate remediation required.",
             "SSHed into {host}. Identified unrotated debug logs in /var/log/app/ exceeding 45GB. Compressed historical logs >7 days into gzip. Purged old stdout.log files. Updated logrotate configuration. Disk usage dropped to 42%."),
            ("Disk full alert: {host} /tmp partition warning",
             "Host {host} reporting 94% inode and disk utilization on /tmp.",
             "Inspected /tmp on {host}. Found leftover docker build caches and orphan core dumps. Removed files older than 3 days. Cleaned systemd journal logs via journalctl --vacuum-time=3d. Usage normalized to 35%."),
            ("Remediate log buildup on worker node {host}",
             "Kubernetes node {host} reporting ephemeral-storage pressure. Pod eviction risk.",
             "Ran crictl rmi --prune to eliminate dangling container images. Cleaned /var/log/pods logs. Node status transitioned back to Ready with 68% free storage."),
            ("Routine storage remediation on {host}",
             "Automated metric alert: /data volume on {host} surpassed 88% watermark.",
             "Analyzed storage breakdown via ncdu. Archived completed batch output files to Cloud Storage bucket gs://coldline-archives/. Freed 120GB.")
        ],
        "hosts": ["gce-prod-api-01", "worker-batch-node-04", "k8s-node-pool-prod-7", "log-aggregator-vm-02", "bastion-relay-01"],
        "percentages": [91, 94, 96, 98, 92]
    },
    "WF_PASSWORD_RESET": {
        "name": "Password Resets and Account Unlocks",
        "description": "Verifying employee identity and resetting locked directory credentials or multi-factor tokens.",
        "category": "Helpdesk",
        "typical_handling_range": (8, 15),  # minutes
        "templates": [
            ("User account locked out after multiple failed attempts: {user}",
             "Employee {user} locked out of corporate Okta/Google Workspace. Self-service reset failed due to expired SMS MFA token.",
             "Verified employee identity via video call and Slack manager verification. Cleared account lockout in Okta Admin console. Generated one-time temporary access token valid 1 hour. Instructed user to register new WebAuthn FIDO key. Confirmed successful login."),
            ("Password expired and cannot login: {user}",
             "My domain password expired over the weekend and I cannot connect to VPN or corporate portal.",
             "Verified identity with badge ID lookup against HR database. Initiated self-service password reset workflow. Reset Active Directory password with 'Must change at next login' flag. Assisted user with Cisco AnyConnect VPN reconnection."),
            ("MFA token desync / new device setup for {user}",
             "Got a replacement company laptop/phone and lost Google Authenticator OTP token for {user}.",
             "Followed out-of-band identity verification protocol. Sent verification code to registered recovery email. Revoked old MFA tokens and enrolled new hardware token. Tested portal sign-in."),
            ("Account unlock request: {user}",
             "Help, typed wrong password 5 times on SSO page. Please unblock account.",
             "Looked up user {user} in directory. Account was in soft-lock state. Manually unlocked account and sent password reset link to verified phone number. Verified incident closed.")
        ]
    },
    "WF_DEPLOY_VALIDATION": {
        "name": "Routine Deployment and Configuration Validation",
        "description": "Post-deployment smoke testing, configuration validation, canary monitoring, and release sign-off.",
        "category": "DevOps",
        "typical_handling_range": (20, 35),  # minutes
        "templates": [
            ("Post-deployment verification for release {version} on {service}",
             "Scheduled release {version} deployed to production. Require manual smoke test, metric verification, and rollback readiness check.",
             "Executed automated post-deploy smoke tests against /healthz and /api/v1/ping. Checked Cloud Monitoring metrics for error rate spikes (5xx rate < 0.01%). Verified ConfigMap and Secret versions match release manifest. Confirmed release {version} stable and notified on-call lead."),
            ("Verify canary rollout of {service} {version}",
             "Traffic routing 10% canary for {service} release {version}. Monitor latency and error budget.",
             "Monitored Prometheus p95 latency and HTTP 500 error counts for 15 minutes. Latency stayed within SLA (<120ms). Compared logs with baseline. Promoted canary to 100% traffic. Sign-off recorded."),
            ("Config drift check and environment validation for {service}",
             "Please verify production configuration parameters for {service} align with staging release {version}.",
             "Extracted Kubernetes deployment yaml and compared with Helm values-prod.yaml. Found no drift. Ran integration health check. Appended validation log to release ticket.")
        ],
        "services": ["payment-gateway", "auth-service", "order-processing-api", "inventory-service", "search-indexer"],
        "versions": ["v2.14.0", "v3.1.2", "v2.15.1", "v4.0.0-rc3", "v1.9.8"]
    },
    "WF_CERT_SERVICE_ACCOUNT": {
        "name": "Service Account and Certificate Renewal Requests",
        "description": "Rotating expiring SSL/TLS certificates and service account keys across clusters and secrets managers.",
        "category": "Security",
        "typical_handling_range": (30, 50),  # minutes
        "templates": [
            ("SSL Certificate expiration warning: {domain} expiring in 14 days",
             "Certificate alert: TLS certificate for {domain} expires on next renewal window. Needs renewal and ingress reload.",
             "Generated new CSR using company CA / Google Certificate Manager. Issued renewed TLS cert with 365-day validity. Updated Secret 'tls-{domain}' in Kubernetes production namespace. Reloaded ingress controller without downtime. Verified handshake using openssl s_client -connect {domain}:443."),
            ("Rotate service account key for {service_account}",
             "Security compliance requirement: Service account key for {service_account} is 90 days old. Rotation required.",
             "Created new key pair for {service_account} via gcloud iam service-accounts keys create. Updated Google Secret Manager secret 'sa-key-{service_account}'. Performed rolling restart of dependent worker pods. Verified worker operational. Deleted deprecated old key from IAM."),
            ("mTLS internal certificate renewal for {domain}",
             "Service mesh mutual TLS certificate expiring for internal endpoint {domain}.",
             "Renewed root-signed client certificate. Distributed cert to Vault storage. Restarted Envoy sidecars. Confirmed mTLS connection status healthy.")
        ],
        "domains": ["api.corp.internal", "portal.payments.net", "staging-gateway.cloud", "auth.sso.internal"],
        "service_accounts": ["sa-bigquery-loader@prod.iam.gserviceaccount.com", "sa-pubsub-subscriber@prod.iam.gserviceaccount.com", "sa-cloudbuild-deployer@prod.iam.gserviceaccount.com"]
    }
}

DEVOPS_PLANTED_WORKFLOWS = {
    "WF_CICD_FLAKY_TEST": {
        "name": "CI/CD Pipeline Failure & Flaky Test Remediation",
        "description": "Flushing runner build cache, re-triggering failed workflow jobs, quarantining flaky tests, and confirming green PR status.",
        "category": "DevOps & CI/CD",
        "typical_handling_range": (20, 40),
        "systems": ["GitHub Actions", "GitLab CI", "Docker Registry"],
        "templates": [
            ("CI/CD pipeline failure on {repo_name} PR #{pr_number}",
             "GitHub Actions runner timed out during integration test suite on branch {branch}. Job failed with exit code 137.",
             "Flushed runner build cache. Inspected test artifact logs; identified flaky timeout in test_payment_webhook. Quarantined flaky test in quarantine.json manifest. Re-triggered workflow job; all 42 checks passed green."),
            ("Docker build layer cache corruption in {repo_name} pipeline",
             "GitLab CI pipeline failed during docker build step: layer cache checksum mismatch on branch {branch}.",
             "Purged remote container registry cache tags. Re-ran pipeline with --no-cache flag. Image built and scanned with Trivy: 0 critical vulnerabilities. Deployed to dev cluster."),
            ("Runner timeout on e2e test suite: {service}",
             "Automated PR merge blocked for {repo_name}. End-to-end regression job exceeded 45-minute timeout threshold.",
             "Identified deadlocked Selenium worker thread. Terminated stuck runner container. Bumped runner parallelism from 4 to 8. Re-executed workflow; build finished in 18 minutes.")
        ],
        "pr_numbers": [1042, 1089, 1120, 1156, 1201],
        "branches": ["feature/auth-v2", "fix/checkout-timeout", "chore/upgrade-deps", "feat/kafka-consumer"]
    },
    "WF_K8S_CRASHLOOP_OOM": {
        "name": "Kubernetes CrashLoopBackOff & OOMKilled Pod Triage",
        "description": "Investigating pod evictions, inspecting container exit codes, adjusting memory limits in Helm/GitOps manifests, and stabilizing workloads.",
        "category": "Platform Engineering",
        "typical_handling_range": (25, 45),
        "systems": ["Kubernetes API", "Prometheus", "Helm"],
        "templates": [
            ("Prometheus Alert: KubePodCrashLooping in namespace {namespace}",
             "Microservice {service} pod in CrashLoopBackOff state. Restart count 14 in last 30 minutes.",
             "Ran kubectl logs --previous to capture crash stack trace. Discovered OutOfMemoryError (exit code 137). Checked Prometheus memory usage graph: peak usage hit 512Mi limit. Updated Helm values.yaml memory request to 512Mi and limit to 1Gi. Applied change via ArgoCD sync. Pod stabilized with 0 restarts."),
            ("OOMKilled alert: {service} worker pod evicted in {namespace}",
             "Production worker pod {service} killed by Linux kernel OOM killer during batch data ingestion.",
             "Inspected kubectl describe pod. Confirmed Last State: Terminated with Reason: OOMKilled. Increased JVM heap max ratio in ConfigMap. Rolled out updated deployment. Monitored memory consumption for 20 mins; memory stabilized at 65%."),
            ("Pod eviction in namespace {namespace} due to node memory pressure",
             "Multiple pods evicted on node {host}. Service {service} degraded.",
             "Cordoned and drained worker node {host}. Identified memory leak in {service} background task. Applied hotfix deployment and verified pod rescheduling across alternate node pool.")
        ],
        "namespaces": ["production-core", "payments-staging", "data-analytics", "ingress-system"]
    },
    "WF_TERRAFORM_LOCK": {
        "name": "Terraform State Lock & IaC Drift Remediation",
        "description": "Investigating stuck apply operations, safely unlocking DynamoDB/GCS state locks, diffing plan outputs, and resolving IaC drift.",
        "category": "Infrastructure as Code",
        "typical_handling_range": (15, 30),
        "systems": ["Terraform Cloud", "AWS DynamoDB", "Google Cloud Storage"],
        "templates": [
            ("Terraform state lock acquisition failure on {resource}",
             "Pipeline blocked: Error acquiring state lock: DynamoDB lock table item already exists for lock ID {lock_id}.",
             "Verified no concurrent apply or plan jobs running in CI. Validated engineer who initiated prior plan had aborted terminal session. Executed terraform force-unlock {lock_id}. Ran terraform plan to verify state lock cleared and clean drift status."),
            ("IaC drift detected on cloud resource {resource}",
             "Nightly drift detection run flagged discrepancy between Terraform state and live cloud infrastructure.",
             "Generated refreshed terraform plan. Identified manual tag modification applied via Cloud Console. Imported updated attributes into Terraform configuration file. Committed PR to GitOps repo; re-applied state with zero infrastructure changes."),
            ("GCS state backend lock deadlock on env {env_id}",
             "Staging deployment halted: Error locking state in GCS bucket gs://tf-state-{env_id}.",
             "Inspected GCS object metadata. Cleared stale lock generation ID. Validated state file integrity with terraform state list. Deployment pipeline resumed successfully.")
        ],
        "lock_ids": ["a4f81c90-93bc-4b12", "b7e22d11-88fc-4c91", "c1a99f02-12aa-4188"]
    },
    "WF_DB_MIGRATION_LOCK": {
        "name": "Database Migration Lock & Replica Lag Remediation",
        "description": "Resolving schema migration lock deadlocks, diagnosing long-running queries, and mitigating read-replica replication lag.",
        "category": "Database Reliability (DBRE)",
        "typical_handling_range": (30, 50),
        "systems": ["PostgreSQL", "Cloud SQL", "Flyway"],
        "templates": [
            ("Release blocked: Schema migration waiting for table lock on {service}",
             "Flyway schema migration in release pipeline hanging for >15 minutes: Waiting for AccessExclusiveLock on table orders.",
             "Queried pg_stat_activity to inspect active transactions. Discovered unindexed analytical query running for 2.4 hours holding lock. Notified query owner. Terminated blocking PID using pg_terminate_backend. Migration resumed immediately and completed in 8 seconds. Release unblocked."),
            ("Cloud SQL read replica replication lag > 300s alert",
             "Prometheus alert: Database replica replication lag exceeded 350 seconds. Read traffic failing.",
             "Inspected replica status using SHOW SLAVE STATUS / pg_stat_replication. Found lock contention caused by heavy bulk update transaction. Temporarily diverted read traffic to primary instance. Increased IOPS allocation. Replication lag recovered to 0.4s."),
            ("Deadlock detected during foreign key migration: {service}",
             "Deployment rollback triggered: Deadlock detected between background celery worker and migration DDL.",
             "Temporarily paused Celery task queue consumption. Re-executed schema migration script in isolated transaction. Successfully created foreign key with NOT VALID clause and validated asynchronously. Resumed worker queues.")
        ]
    },
    "WF_KAFKA_CONSUMER_LAG": {
        "name": "Kafka Consumer Group Rebalance Lag & DLQ Message Drain",
        "description": "Diagnosing partition rebalance storms, clearing dead-letter queue backlogs, and adjusting consumer poll timeouts.",
        "category": "Distributed Messaging",
        "typical_handling_range": (20, 35),
        "systems": ["Apache Kafka", "Confluent Cloud", "KEDA"],
        "templates": [
            ("Kafka consumer group lag alert: topic {service}-events lagging {pct}k msgs",
             "Prometheus alert: consumer group {service}-workers falling behind SLA. Rebalance loop detected.",
             "Inspected consumer pod metrics. Found heartbeating thread starvation caused by blocking external call. Increased max.poll.interval.ms to 300000ms. Drained unprocessable poison-pill messages to DLQ topic. Consumer group caught up in 8 minutes."),
            ("Partition rebalance storm on cluster {host}",
             "Kafka broker reporting frequent consumer group coordinator rebalances on {resource}.",
             "Identified unstable pod restarts triggering continuous consumer rebalances. Upgraded consumer group assignment strategy to CooperativeStickyAssignor. Verified lag reduced to 0.")
        ]
    },
    "WF_AWS_ASSUMEROLE_TIMEOUT": {
        "name": "Cloud Cross-Account IAM AssumeRole Timeout Recovery",
        "description": "Refreshing expired STS session credentials, auditing cross-account trust policies, and recovering pipeline authentication.",
        "category": "Cloud Security",
        "typical_handling_range": (15, 28),
        "systems": ["AWS STS", "IAM", "Google Cloud Workload Identity"],
        "templates": [
            ("Cross-account AssumeRole session expired on {service}",
             "CI deployment failed: ExpiredToken: The security token included in the request is expired during STS assume_role.",
             "Validated Workload Identity Federation provider claims. Updated STS role session duration from 1800s to 3600s. Refreshed cached ephemeral token in GitHub Secrets. Re-triggered build; AWS credentials validated successfully."),
            ("IAM trust policy denied AssumeRole on {resource}",
             "Production data pipeline failed with AccessDenied: sts:AssumeRole not authorized for principal {role}.",
             "Checked IAM trust relationship on destination account. Added external ID to trust policy. Tested STS AssumeRole via aws cli; session credentials returned valid token.")
        ]
    }
}

CORE_DEVOPS_PLANTED_WORKFLOWS = {
    k: DEVOPS_PLANTED_WORKFLOWS[k]
    for k in ["WF_CICD_FLAKY_TEST", "WF_K8S_CRASHLOOP_OOM", "WF_TERRAFORM_LOCK", "WF_DB_MIGRATION_LOCK"]
}

MANUFACTURING_PLANTED_WORKFLOWS = {
    "WF_SAP_GUI_RESET": {
        "name": "SAP ERP GUI Terminal Session Reset & Print Spool Unlock",
        "description": "Clearing locked SAP user transaction sessions (SM04/SM12), resetting hung background spool jobs (SP01), and restoring warehouse terminal access.",
        "category": "Enterprise ERP",
        "typical_handling_range": (15, 28),
        "systems": ["SAP S/4HANA", "SAP GUI", "Zebra Print Server"],
        "templates": [
            ("SAP session locked for user {user} in warehouse terminal {host}",
             "Warehouse operator {user} unable to process shipping orders. SAP GUI locked with error: User already logged on in client 100.",
             "Logged into SAP management console. Ran transaction SM04; located orphan GUI terminal session on terminal {host}. Terminated hung GUI process. Checked lock entries in SM12; cleared exclusive table lock on VBAK. User confirmed barcode scanning resumed."),
            ("SAP spool job stuck in status 'Printing' for packing line {host}",
             "Packing line label printer queue halted. SAP spool request #998124 hanging in output status.",
             "Accessed transaction SP01. Found dead socket connection to network print server. Cancelled stuck spool request and re-routed print queue to backup thermal printer. Verified packing slip printing resumed.")
        ]
    },
    "WF_PLC_EDGE_GATEWAY": {
        "name": "PLC & Assembly Line Edge Gateway Firmware Resync",
        "description": "Diagnosing Siemens/Allen-Bradley industrial IoT gateway connection drops, restarting edge telemetry daemons, and resyncing sensor polling loops.",
        "category": "Industrial IoT & OT",
        "typical_handling_range": (25, 45),
        "systems": ["Siemens S7 PLC", "Moxa Edge Gateway", "Kepware OPC-UA"],
        "templates": [
            ("Edge gateway {host} communication timeout with Assembly Line PLC",
             "Manufacturing execution system (MES) reporting telemetry loss from Line 3 PLC controller. Cycle time monitoring offline.",
             "Verified physical switch link on OT VLAN. SSHed into Moxa edge gateway {host}. Found memory leak in edge forwarder daemon. Restarted gateway telemetry service via systemctl restart ot-collector. Verified Modbus TCP handshake to PLC restored (latency 4ms)."),
            ("PLC gateway packet drop alert on packaging conveyor {host}",
             "Line supervisor reports intermittent sensor data dropouts from conveyor torque sensors.",
             "Inspected Ethernet/IP ring topology. Replaced degraded industrial RJ45 patch cable. Power-cycled edge interface module. Confirmed 0 CRC packet errors over 20-minute soak test.")
        ]
    },
    "WF_SCADA_OPCUA_SYNC": {
        "name": "SCADA Sensor Telemetry Dropout & OPC-UA Reconnection",
        "description": "Renewing expired OPC-UA security certificates, restarting Kepware tag servers, and recovering real-time plant SCADA telemetry feeds.",
        "category": "Plant Operations & SCADA",
        "typical_handling_range": (20, 35),
        "systems": ["Ignition SCADA", "OPC-UA", "KepserverEx"],
        "templates": [
            ("SCADA server reporting OPC-UA communication failure on {service}",
             "Ignition SCADA dashboard showing Bad_CommunicationError on tag group Boiler-Telemetry-01.",
             "Inspected OPC-UA client connection status in Ignition Gateway. Discovered server endpoint certificate expired. Generated renewed X.509 endpoint certificate in Kepware security store. Re-established trusted mutual certificate pairing. Tag quality returned to Good across all 140 sensors."),
            ("Tag polling latency spike on plant SCADA server {host}",
             "SCADA control room alarms delayed by >8 seconds. Tag scan rate degraded.",
             "Analyzed OPC-UA server diagnostic logs. Identified thread pool saturation from orphaned client sessions. Restarted Kepware service. Tag scan rate normalized to 250ms SLA.")
        ]
    },
    "WF_SUPPLY_CHAIN_IAM": {
        "name": "Supplier Portal B2B Partner Credential & Token Renewal",
        "description": "Provisioning external vendor EDI/AS2 credentials, resetting expired partner portal tokens, and auditing third-party supplier access.",
        "category": "Supply Chain IAM",
        "typical_handling_range": (15, 30),
        "systems": ["Supplier Connect Portal", "Azure AD B2B", "Sterling Commerce"],
        "templates": [
            ("Vendor logistics coordinator {user} locked out of Supplier Portal",
             "Tier-1 parts supplier coordinator {user} unable to submit Advance Shipping Notice (ASN). Partner account expired.",
             "Verified vendor contract status with procurement officer. Re-enabled B2B external collaboration account in Azure AD B2B. Extended account validity by 90 days. Sent self-service MFA reset link. Supplier confirmed successful ASN submission."),
            ("AS2 partner trading partner certificate expired for {service}",
             "Inbound EDI purchase orders failing: AS2 decryption failed for partner {service}.",
             "Received updated public signing certificate from vendor security team. Imported certificate into AS2 server keystore. Tested test EDI 850 document transmission; partner confirmed MDN receipt.")
        ]
    },
    "WF_BARCODE_SCANNER_WIFI": {
        "name": "Zebra Factory Floor Handheld Scanner Wi-Fi Handshake Fix",
        "description": "Clearing 802.1x roaming authentication lockouts on Zebra Android scanners, resetting MDM profiles, and re-enrolling warehouse devices.",
        "category": "Plant Floor Mobility",
        "typical_handling_range": (12, 22),
        "systems": ["Zebra TC57", "SOTI MobiControl MDM", "Cisco Catalyst Wireless"],
        "templates": [
            ("Handheld scanner {host} failing Wi-Fi authentication on plant floor",
             "Order picking stopped in aisle 14. Zebra terminal {host} unable to associate with WPA2-Enterprise SSID.",
             "Checked Cisco ISE RADIUS logs; identified expired machine certificate on device. Pushed updated SOTI MDM Wi-Fi profile over cellular fallback. Power-cycled device. Terminal authenticated successfully to plant-wlan-01 with -58 dBm signal."),
            ("Barcode scanner app freezing on inventory scan: device {host}",
             "Warehouse picker reporting scanner laser triggering but enterprise warehouse app unresponsive.",
             "Remotely inspected device via MDM console. Cleared app data cache for WarehousePro. Re-synced offline lookup database. Verified test scan resolved item SKU immediately.")
        ]
    },
    "WF_SAP_IDOC_QUEUE": {
        "name": "Stuck SAP IDoc Transaction & EDI Purchase Order Queue Clear",
        "description": "Investigating stuck inbound/outbound IDocs (status 51/64), correcting EDI segment errors, and reprocessing failed ERP purchase orders.",
        "category": "ERP & Logistics EDI",
        "typical_handling_range": (20, 40),
        "systems": ["SAP BD87", "WE02", "Sterling Integrator"],
        "templates": [
            ("Critical: 48 SAP IDocs stuck in status 51 for sales orders",
             "Customer delivery orders blocked. Inbound ORDERS05 IDocs failing with error: Material master missing sales view.",
             "Ran transaction BD87 in SAP production. Identified missing sales organization view for new SKU #88192. Coordinated with master data team to maintain sales view. Re-processed failed IDoc queue via BD87; all 48 IDocs transitioned to status 53 (Success). Sales orders created."),
            ("Outbound DESADV delivery notice IDocs stuck in queue {resource}",
             "Outbound shipping notifications to freight carriers not sending. IDoc status 30.",
             "Investigated transactional RFC (SM58). Found hung tRFC queue due to carrier partner endpoint timeout. Cleared blocked queue entry. Re-triggered RSARFCEX background report. 112 delivery notices dispatched successfully.")
        ]
    }
}

BANKING_PLANTED_WORKFLOWS = {
    "WF_SWIFT_MT103_TLS": {
        "name": "SWIFT MT103 Interbank Gateway TLS Certificate Rotation",
        "description": "Rotating mutual TLS certificates on SWIFT Alliance Gateway, verifying HSM signing keys, and confirming international wire settlement routing.",
        "category": "Payment Systems",
        "typical_handling_range": (30, 55),
        "systems": ["SWIFT Alliance Gateway", "Thales Luna HSM", "Finastra"],
        "templates": [
            ("SWIFT Gateway TLS certificate expiring in 7 days on node {host}",
             "Compliance alert: Mutual TLS certificate on SWIFT Alliance Gateway {host} reaching 365-day expiration window. Wire cutoff at 17:00 EST.",
             "Generated 4096-bit RSA CSR using Hardware Security Module (HSM). Submitted CSR to corporate PKI. Deployed approved cert into SWIFT Alliance Gateway keystore. Executed health check ping to SWIFT test network. Swapped live traffic during low-volume settlement window. Verified handshake 200 OK without dropping wire traffic."),
            ("SWIFT wire message parsing warning on gateway {host}",
             "Alliance Access reporting validation warning on incoming MT103 message format header.",
             "Inspected SWIFT BIC directory version. Synchronized latest BIC Plus monthly delta file. Re-validated message syntax; wire transmission unblocked.")
        ]
    },
    "WF_LEDGER_RECONCILE": {
        "name": "Core Banking Ledger Settlement Discrepancy Triage",
        "description": "Investigating automated end-of-day general ledger balancing discrepancies, auditing transaction settlement batches, and resolving rounding mismatches.",
        "category": "Core Banking",
        "typical_handling_range": (35, 60),
        "systems": ["Temenos Transact", "Oracle Financials", "Kafka Financial Stream"],
        "templates": [
            ("End-of-day ledger mismatch: Clearing account balance off by $4,120.50",
             "Daily automated balance reconciliation job flagged discrepancy between ACH clearing sub-ledger and GL control account.",
             "Queried SQL settlement ledger for timestamp window 23:00-00:00. Located duplicate settlement event caused by network retry from debit card gateway. Prepared compensatory journal adjustment entry. Obtained VP Finance dual-authorization sign-off. Applied GL adjustment. Ledger balanced with zero net variance."),
            ("Foreign exchange FX settlement variance in euro clearing queue",
             "Automated cross-currency wire batch reported $84.20 rounding discrepancy in EUR/USD spot conversion.",
             "Inspected Reuters real-time FX rate snapshot at transaction execution time. Corrected micro-precision rounding error in settlement conversion service. Posted rebalancing entry.")
        ]
    },
    "WF_AML_SANCTION_CLEAR": {
        "name": "Anti-Money Laundering (AML) Sanction Screen False-Positive Clear",
        "description": "Reviewing automated OFAC/PEP sanction screening hits, comparing corporate beneficial ownership registries, and releasing blocked customer wire transfers.",
        "category": "Financial Crime & Compliance",
        "typical_handling_range": (20, 35),
        "systems": ["Fircosoft AML", "LexisNexis WorldCompliance", "FinCEN Registry"],
        "templates": [
            ("Wire transfer #889124 blocked by OFAC Sanction Screening hit",
             "Outbound wire payment of $150,000 held in quarantine. Remitter name matched Specially Designated Nationals (SDN) partial fuzzy hit.",
             "Conducted Level-2 compliance review. Compared recipient date of birth, passport country, and address against OFAC SDN database. Confirmed false positive match on common patronymic surname. Attached compliance verification dossier to audit case. Released payment from AML quarantine queue."),
            ("Politically Exposed Person (PEP) screening flag on commercial deposit",
             "Automated onboarding AML check flagged new corporate treasury account signer as PEP match.",
             "Reviewed LexisNexis WorldCompliance report. Validated individual is distant non-immediate relative with zero controlling interest. Logged Enhanced Due Diligence (EDD) sign-off; approved account opening.")
        ]
    },
    "WF_BLOOMBERG_KERBEROS": {
        "name": "Bloomberg Terminal & Trade Station Dual-Factor Kerberos Unlock",
        "description": "Unlocking fixed-income/equities trader workstation credentials, re-authorizing Bloomberg B-Unit biometric tokens, and resetting Kerberos tickets.",
        "category": "Trading Desk Tech",
        "typical_handling_range": (10, 20),
        "systems": ["Bloomberg Professional", "Active Directory Kerberos", "B-Unit"],
        "templates": [
            ("Trader {user} locked out of Bloomberg terminal on trading desk {host}",
             "URGENT: Senior Equities Trader {user} locked out during market pre-open. Bloomberg B-Unit biometric rejected fingerprint 3 times.",
             "Verified trader identity via recorded desk phone line and managing director approval. Reset Kerberos TGT ticket on Active Directory domain controller. Re-synchronized trader's physical Bloomberg B-Unit fingerprint scanner via Bloomberg Admin portal. Trader signed in successfully 12 minutes before market open."),
            ("Trade execution terminal dual-monitor video lock on desk {host}",
             "FX trading workstation frozen with Bloomberg launchpad unresponsive.",
             "Remotely terminated hung Bloomberg win_api process. Flushed temporary terminal cache. Trader resumed live currency quote monitoring.")
        ]
    },
    "WF_FEDRAMP_HSM_KEY": {
        "name": "Cloud HSM Key Attestation & Encryption Envelope Rotation",
        "description": "Validating FIPS 140-2 Level 3 hardware security module attestation statements, rotating customer data encryption keys (DEK), and logging compliance proofs.",
        "category": "FinTech Security & Cryptography",
        "typical_handling_range": (25, 45),
        "systems": ["AWS CloudHSM", "Google Cloud KMS", "Vault HSM"],
        "templates": [
            ("FedRAMP quarterly compliance: HSM cryptographic key attestation required",
             "Security audit requirement: Verify that payment database envelope master keys reside exclusively inside FIPS 140-2 Level 3 HSM hardware.",
             "Executed HSM CLI key attestation command. Verified SHA-256 certificate signature chain against Thales hardware root CA. Exported tamper-evident cryptographic attestation manifest. Attached report to SOC2 compliance auditor evidence portal."),
            ("Data encryption key (DEK) envelope rotation for cardholder database",
             "PCI-DSS quarterly compliance mandate: Rotate symmetric AES-256 key for primary account number (PAN) storage.",
             "Triggered automated envelope key rotation via Cloud KMS. Re-encrypted sample batch to verify backward decryption compatibility. Logged cryptographic audit hash.")
        ]
    },
    "WF_EOD_BATCH_DEADLOCK": {
        "name": "End-of-Day Settlement Batch Job Deadlock Recovery",
        "description": "Mitigating overnight batch settlement process deadlocks, terminating orphaned database locks, and resuming interest accrual calculation pipelines.",
        "category": "Capital Markets Operations",
        "typical_handling_range": (30, 50),
        "systems": ["Control-M", "IBM MQ", "Oracle Exadata"],
        "templates": [
            ("Control-M job EOD_SETTLE_BATCH_04 failed with ORA-00060 Deadlock",
             "Overnight interest calculation pipeline halted at step 8 of 12. Overnight ACH settlement transmission window closing in 45 mins.",
             "Analyzed Oracle v$lock table. Found deadlock between overnight loan interest accrual job and delayed mortgage payment batch. Terminated blocking shadow session. Reran batch job with optimized table partition locks. Pipeline finished in 22 minutes; clearing window met successfully."),
            ("IBM MQ queue depth warning on settlement transaction queue {resource}",
             "Message queue {resource} depth reached 95% capacity. Batch consumer not keeping pace with wire volume.",
             "Allocated 4 additional batch consumer worker instances in Control-M scheduler. Monitored message consumption; queue drained to 0 in 14 minutes.")
        ]
    }
}

ONE_OFF_TEMPLATES = [
    ("Broken laptop monitor / HDMI port flickering", "Laptop HDMI display flickers when connecting to external monitor at desk 4B.", "Hardware Support", 35, "Replaced faulty USB-C dongle and verified display output."),
    ("Conference room C Zoom room audio echo", "During all-hands meeting, microphones in Conf Room C cause severe echo.", "Facilities IT", 45, "Recalibrated ceiling microphone array and updated Zoom Rooms controller firmware."),
    ("Coffee machine smart display network offline", "Breakroom IoT touch panel not connecting to guest WiFi.", "Facilities IT", 20, "Rebooted local AP and rejoined IoT MAC address to isolated VLAN."),
    ("Keyboard sticky keys after coffee spill", "Spilled coffee on mechanical keyboard. Spacebar and enter keys sticking.", "Hardware Support", 15, "Swapped damaged keyboard with new standard-issue peripheral from IT depot."),
    ("Custom SQL query syntax error in reporting dashboard", "Getting syntax error 1064 in custom SQL query in Looker Studio report.", "Data Support", 55, "Assisted user with dialect syntax. Fixed unescaped reserved word in GROUP BY clause."),
    ("Third-party vendor API unexpected 502 Bad Gateway", "Stripe webhook integration returning intermittent 502 gateway errors.", "Third-Party Incidents", 60, "Checked Stripe status page; identified vendor incident. Subscribed to status updates and monitored resolution."),
    ("Slow WiFi in engineering annex 3rd floor", "Multiple users reporting packet loss and high latency on corporate-secure SSID.", "Network IT", 50, "Investigated Meraki dashboard. Found radio interference on channel 6. Switched AP to DFS channel; SNR normalized."),
    ("Need ergonomic mouse recommendation", "Ergonomic assessment suggested vertical mouse for wrist strain.", "IT Procurement", 10, "Approved standard Logitech MX Vertical requisition from IT equipment catalog."),
    ("Excel crashing when opening 500MB CSV file", "Finance analyst reporting Excel memory limit exceeded when opening client transaction dump.", "Desktop Support", 25, "Guided user to open dataset in BigQuery / Python Pandas instead of 32-bit Excel."),
    ("Printer paper jam on 2nd floor copier", "Copier Tray 2 jammed during print run of quarterly slides.", "Facilities IT", 15, "Cleared paper path obstruction in duplexing unit. Tested test print sheet successfully.")
]

ENGINEERS = [
    "Alex Chen (SRE)", "Priya Sharma (Cloud Ops)", "Marcus Vance (DevOps)", 
    "Jordan Taylor (IT Support)", "Elena Rostova (SecOps)", "David Kim (Platform Eng)",
    "Samira Khan (Cloud Identity)", "Carlos Mendez (Systems Eng)"
]

USER_NAMES = [
    "r.patel", "m.smith", "j.kowalski", "s.garcia", "t.nakamura", 
    "l.dupont", "a.fischer", "k.johansson", "v.singh", "b.williams"
]


def _introduce_noise(text: str, noise_type: str) -> str:
    """Adds realistic noise: typos, abbreviations, casing inconsistency."""
    if noise_type == "typo":
        replacements = [
            ("password", "pawword"), ("access", "acces"), ("environment", "enviornment"),
            ("staging", "stagging"), ("cleanup", "clenup"), ("storage", "stroage"),
            ("permission", "permision"), ("certificate", "certifcate"), ("account", "acct"),
            ("urgent", "urgnt"), ("database", "db"), ("restart", "restrt")
        ]
        for src, dst in replacements:
            if src in text.lower() and random.random() < 0.3:
                return text.replace(src, dst)
    elif noise_type == "abbrev":
        replacements = [
            ("production", "prod"), ("development", "dev"), ("administrator", "admin"),
            ("configuration", "config"), ("repository", "repo"), ("application", "app"),
            ("service account", "SA"), ("kubernetes", "k8s")
        ]
        for src, dst in replacements:
            if src in text.lower():
                return text.replace(src, dst)
    return text


def generate_synthetic_dataset(
    num_tickets: int = 3000,
    seed: int = 42,
    start_date: datetime = None,
    include_devops: bool = False
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Generates a deterministic synthetic IT ticket dataset.
    Supports both baseline ITSM workflows (6) and extended DevOps/SRE workflows (10).
    
    Returns:
        (tickets_list, ground_truth_manifest)
    """
    random.seed(seed)
    if start_date is None:
        start_date = datetime(2025, 10, 1, 8, 0, 0)
    
    # Target distribution of tickets:
    # 75% planted repetitive workflows, 25% one-off noise tickets
    num_planted = int(num_tickets * 0.75)
    num_one_offs = num_tickets - num_planted
    
    # Select active workflows and weights
    if include_devops:
        active_wf = {**PLANTED_WORKFLOWS, **CORE_DEVOPS_PLANTED_WORKFLOWS}
        wf_keys = list(active_wf.keys())
        wf_weights = [0.12, 0.10, 0.10, 0.14, 0.09, 0.08, 0.10, 0.10, 0.09, 0.08]
    else:
        active_wf = PLANTED_WORKFLOWS
        wf_keys = list(PLANTED_WORKFLOWS.keys())
        wf_weights = [0.20, 0.14, 0.17, 0.24, 0.13, 0.12]
    
    planted_counts = {wf: 0 for wf in wf_keys}
    tickets = []
    
    # Ground truth summary for evaluation comparison
    ground_truth_stats = {
        "seed": seed,
        "total_tickets": num_tickets,
        "planted_total": num_planted,
        "one_off_total": num_one_offs,
        "workflows": {
            wf: {
                "name": active_wf[wf]["name"],
                "count": 0,
                "total_handling_minutes": 0.0,
                "expected_hours_total": 0.0
            } for wf in wf_keys
        }
    }
    
    ticket_counter = 1
    
    # 1. Generate planted repetitive tickets
    for _ in range(num_planted):
        wf_key = random.choices(wf_keys, weights=wf_weights, k=1)[0]
        wf_meta = active_wf[wf_key]
        planted_counts[wf_key] += 1
        
        tmpl = random.choice(wf_meta["templates"])
        title_fmt, desc_fmt, res_fmt = tmpl
        
        # Format variables
        ctx = {
            "user": random.choice(USER_NAMES),
            "role": random.choice(wf_meta.get("roles", ["Viewer"])),
            "resource": random.choice(wf_meta.get("resources", ["cloud-prod"])),
            "group": random.choice(wf_meta.get("groups", ["all-engineers"])),
            "repo_name": random.choice(wf_meta.get("repos", ["main-app"])),
            "env_id": random.choice(wf_meta.get("envs", ["staging-01"])),
            "host": random.choice(wf_meta.get("hosts", ["srv-01"])),
            "pct": random.choice(wf_meta.get("percentages", [95])),
            "service": random.choice(wf_meta.get("services", ["core-api"])),
            "version": random.choice(wf_meta.get("versions", ["v1.0.0"])),
            "domain": random.choice(wf_meta.get("domains", ["app.internal"])),
            "service_account": random.choice(wf_meta.get("service_accounts", ["sa@proj.iam.gserviceaccount.com"])),
            "pr_number": random.choice(wf_meta.get("pr_numbers", [1042])),
            "branch": random.choice(wf_meta.get("branches", ["main"])),
            "namespace": random.choice(wf_meta.get("namespaces", ["production"])),
            "lock_id": random.choice(wf_meta.get("lock_ids", ["lock-991"]))
        }
        
        title = title_fmt.format(**ctx)
        desc = desc_fmt.format(**ctx)
        res_notes = res_fmt.format(**ctx)
        
        # Inject realistic noise: 20% typos, 25% abbreviations
        if random.random() < 0.20:
            title = _introduce_noise(title, "typo")
            desc = _introduce_noise(desc, "typo")
        elif random.random() < 0.25:
            title = _introduce_noise(title, "abbrev")
        
        # Handling time (ground truth)
        min_h, max_h = wf_meta["typical_handling_range"]
        # Add normal jitter
        handling_mins = round(max(3.0, random.gauss((min_h + max_h) / 2.0, (max_h - min_h) / 4.0)), 1)
        
        # Realistic timestamp over 90 days
        day_offset = random.randint(0, 90)
        hour_offset = random.randint(7, 19)
        minute_offset = random.randint(0, 59)
        created_dt = start_date + timedelta(days=day_offset, hours=hour_offset, minutes=minute_offset)
        
        # Resolution elapsed time (includes queue wait + active handling)
        # Note: Active handling time != elapsed calendar time!
        queue_wait_minutes = random.randint(10, 480)
        elapsed_minutes = queue_wait_minutes + int(handling_mins)
        resolved_dt = created_dt + timedelta(minutes=elapsed_minutes)
        
        # Priority distribution: mostly Medium/High
        priority = random.choices(["Low", "Medium", "High", "Critical"], weights=[0.15, 0.50, 0.25, 0.10], k=1)[0]
        
        ticket_id = f"TICK-{ticket_counter:05d}"
        ticket_counter += 1
        
        ticket_record = {
            "ticket_id": ticket_id,
            "title": title,
            "description": desc,
            "category": wf_meta["category"],
            "priority": priority,
            "created_at": created_dt.isoformat(),
            "resolved_at": resolved_dt.isoformat(),
            "assignee": random.choice(ENGINEERS),
            "resolution_notes": res_notes,
            "status": "Closed",
            # Hidden evaluation fields ONLY
            "workflow_ground_truth": wf_key,
            "handling_minutes_ground_truth": handling_mins
        }
        tickets.append(ticket_record)
        
        # Accumulate ground truth stats
        ground_truth_stats["workflows"][wf_key]["count"] += 1
        ground_truth_stats["workflows"][wf_key]["total_handling_minutes"] += handling_mins

    # 2. Generate one-off noise tickets
    for _ in range(num_one_offs):
        one_off = random.choice(ONE_OFF_TEMPLATES)
        title, desc, cat, base_mins, res_note = one_off
        
        handling_mins = round(max(5.0, random.gauss(base_mins, 8.0)), 1)
        day_offset = random.randint(0, 90)
        created_dt = start_date + timedelta(days=day_offset, hours=random.randint(8, 18), minutes=random.randint(0, 59))
        resolved_dt = created_dt + timedelta(minutes=random.randint(30, 600) + int(handling_mins))
        
        ticket_id = f"TICK-{ticket_counter:05d}"
        ticket_counter += 1
        
        ticket_record = {
            "ticket_id": ticket_id,
            "title": title,
            "description": desc,
            "category": cat,
            "priority": random.choice(["Low", "Medium", "High"]),
            "created_at": created_dt.isoformat(),
            "resolved_at": resolved_dt.isoformat(),
            "assignee": random.choice(ENGINEERS),
            "resolution_notes": res_note,
            "status": "Closed",
            # Ground truth: None / ONE_OFF
            "workflow_ground_truth": "ONE_OFF",
            "handling_minutes_ground_truth": handling_mins
        }
        tickets.append(ticket_record)

    # Shuffle dataset to mix planted and one-off tickets thoroughly
    random.shuffle(tickets)
    
    # Calculate final ground truth hours
    for wf in wf_keys:
        mins = ground_truth_stats["workflows"][wf]["total_handling_minutes"]
        ground_truth_stats["workflows"][wf]["expected_hours_total"] = round(mins / 60.0, 2)
        
    return tickets, ground_truth_stats


def save_dataset_to_csv(tickets: List[Dict[str, Any]], filepath: str, include_ground_truth: bool = True) -> None:
    """Saves tickets to CSV format."""
    if not tickets:
        return
    
    fieldnames = list(tickets[0].keys())
    if not include_ground_truth:
        fieldnames = [f for f in fieldnames if not f.endswith("_ground_truth")]
        
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for t in tickets:
            row = {k: t[k] for k in fieldnames}
            writer.writerow(row)


def generate_tenant_tickets(tenant_id: str, count: int = 250, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generates industry-specific synthetic tickets partitioned by tenant_id.
    - tenant_acme_global: Manufacturing / ERP (SAP, PLC, SCADA, Zebra)
    - tenant_apex_bank: Regulated Banking / FinTech (SWIFT, Ledger, AML, Bloomberg)
    - tenant_cloudscale: Cloud-Native DevOps / SRE (K8s, Kafka, Terraform, STS)
    - tenant_demo_sandbox: Baseline ITSM (Access, Environment, Log Cleanup, Password)
    """
    random.seed(seed)
    start_date = datetime(2025, 10, 1, 8, 0, 0)
    
    if tenant_id == "tenant_acme_global":
        active_wfs = MANUFACTURING_PLANTED_WORKFLOWS
        prefix = "ACME"
    elif tenant_id == "tenant_apex_bank":
        active_wfs = BANKING_PLANTED_WORKFLOWS
        prefix = "APEX"
    elif tenant_id == "tenant_cloudscale":
        active_wfs = DEVOPS_PLANTED_WORKFLOWS
        prefix = "SRE"
    else:
        active_wfs = PLANTED_WORKFLOWS
        prefix = "DEMO"
        
    wf_keys = list(active_wfs.keys())
    num_planted = int(count * 0.80)
    num_one_offs = count - num_planted
    
    tickets = []
    ticket_counter = 1
    
    for _ in range(num_planted):
        wf_key = random.choice(wf_keys)
        wf_meta = active_wfs[wf_key]
        tmpl = random.choice(wf_meta["templates"])
        title_fmt, desc_fmt, res_fmt = tmpl
        
        ctx = {
            "user": random.choice(USER_NAMES),
            "role": random.choice(wf_meta.get("roles", ["Operator", "Analyst", "Engineer"])),
            "resource": random.choice(wf_meta.get("resources", ["prod-system-01", "queue-primary", "sap-cluster"])),
            "group": random.choice(wf_meta.get("groups", ["operations-l2", "finance-clearing", "manufacturing-ot"])),
            "host": random.choice(wf_meta.get("hosts", ["terminal-p01", "gw-moxa-02", "srv-swift-01", "k8s-worker-09"])),
            "service": random.choice(wf_meta.get("services", ["core-ledger", "sap-orders", "kafka-broker-02", "plc-gateway"])),
            "pct": random.choice([92, 95, 98, 88]),
            "repo_name": random.choice(wf_meta.get("repos", ["payment-gateway", "checkout-api", "inventory-service"])),
            "pr_number": random.choice(wf_meta.get("pr_numbers", [1042, 1150, 1289])),
            "branch": random.choice(wf_meta.get("branches", ["main", "feature/auth", "hotfix/k8s-oom"])),
            "namespace": random.choice(wf_meta.get("namespaces", ["production-core", "payments-staging", "data-analytics"])),
            "env_id": random.choice(wf_meta.get("envs", ["prod-east-1", "staging-02", "us-central1"])),
            "lock_id": random.choice(wf_meta.get("lock_ids", ["a4f81c90-93bc-4b12", "b7e22d11-88fc-4c91"])),
            "version": random.choice(wf_meta.get("versions", ["v2.4.1", "v3.0.0-rc2"])),
            "domain": random.choice(wf_meta.get("domains", ["internal.api", "payments.corp"])),
            "service_account": random.choice(wf_meta.get("service_accounts", ["sa-cloudscale-sre@prod.iam.gserviceaccount.com"]))
        }

        class SafeDict(dict):
            def __missing__(self, key):
                return key
        
        safe_ctx = SafeDict(ctx)
        title = title_fmt.format_map(safe_ctx)
        desc = desc_fmt.format_map(safe_ctx)
        res_notes = res_fmt.format_map(safe_ctx)
        
        min_h, max_h = wf_meta.get("typical_handling_range", (15, 30))
        handling_mins = round(max(5.0, random.gauss((min_h + max_h) / 2.0, (max_h - min_h) / 4.0)), 1)
        
        day_offset = random.randint(0, 90)
        created_dt = start_date + timedelta(days=day_offset, hours=random.randint(7, 19), minutes=random.randint(0, 59))
        resolved_dt = created_dt + timedelta(minutes=random.randint(15, 300) + int(handling_mins))
        
        t_id = f"{prefix}-{ticket_counter:05d}"
        ticket_counter += 1
        
        tickets.append({
            "ticket_id": t_id,
            "tenant_id": tenant_id,
            "title": title,
            "description": desc,
            "category": wf_meta.get("category", "Operations"),
            "priority": random.choice(["Low", "Medium", "High", "Critical"]),
            "created_at": created_dt.isoformat(),
            "resolved_at": resolved_dt.isoformat(),
            "assignee": random.choice(ENGINEERS),
            "resolution_notes": res_notes,
            "status": "Closed",
            "workflow_ground_truth": wf_key,
            "handling_minutes_ground_truth": handling_mins
        })
        
    for _ in range(num_one_offs):
        one_off = random.choice(ONE_OFF_TEMPLATES)
        title, desc, cat, base_mins, res_note = one_off
        handling_mins = round(max(5.0, random.gauss(base_mins, 8.0)), 1)
        day_offset = random.randint(0, 90)
        created_dt = start_date + timedelta(days=day_offset, hours=random.randint(8, 18), minutes=random.randint(0, 59))
        resolved_dt = created_dt + timedelta(minutes=random.randint(30, 400) + int(handling_mins))
        
        t_id = f"{prefix}-{ticket_counter:05d}"
        ticket_counter += 1
        
        tickets.append({
            "ticket_id": t_id,
            "tenant_id": tenant_id,
            "title": title,
            "description": desc,
            "category": cat,
            "priority": random.choice(["Low", "Medium", "High"]),
            "created_at": created_dt.isoformat(),
            "resolved_at": resolved_dt.isoformat(),
            "assignee": random.choice(ENGINEERS),
            "resolution_notes": res_note,
            "status": "Closed",
            "workflow_ground_truth": "ONE_OFF",
            "handling_minutes_ground_truth": handling_mins
        })
        
    random.shuffle(tickets)
    return tickets
