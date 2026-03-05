# ════════════════════════════════════════════
#  VaidyaSaarathi — Storage Resources
#  S3 (Audio + FHIR) + DynamoDB (Triage + Patients)
# ════════════════════════════════════════════

# ── S3: Triage Audio Bucket ─────────────────────────────────────────────────

resource "aws_s3_bucket" "audio" {
  bucket = "${local.name_prefix}-audio-${data.aws_caller_identity.current.account_id}"
  tags   = { Name = "${local.name_prefix}-audio" }
}

resource "aws_s3_bucket_versioning" "audio" {
  bucket = aws_s3_bucket.audio.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_public_access_block" "audio" {
  bucket                  = aws_s3_bucket.audio.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "audio" {
  bucket = aws_s3_bucket.audio.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "audio" {
  bucket = aws_s3_bucket.audio.id

  rule {
    id     = "tiering"
    status = "Enabled"
    filter { prefix = "" }

    transition {
      days          = 30
      storage_class = "INTELLIGENT_TIERING"
    }
    transition {
      days          = 365
      storage_class = "GLACIER"
    }
    expiration {
      days = 2555 # 7 years — medical record retention
    }
  }
}

# ── S3: FHIR Bundle Bucket ──────────────────────────────────────────────────

resource "aws_s3_bucket" "fhir" {
  bucket = "${local.name_prefix}-fhir-${data.aws_caller_identity.current.account_id}"
  tags   = { Name = "${local.name_prefix}-fhir" }
}

resource "aws_s3_bucket_public_access_block" "fhir" {
  bucket                  = aws_s3_bucket.fhir.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "fhir" {
  bucket = aws_s3_bucket.fhir.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ── DynamoDB: Triage Records ─────────────────────────────────────────────────

resource "aws_dynamodb_table" "triage" {
  name         = "${local.name_prefix}-triage"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "patient_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  attribute {
    name = "idempotency_key"
    type = "S"
  }

  # GSI 1 — per-patient triage history
  global_secondary_index {
    name            = "patient_id-index"
    hash_key        = "patient_id"
    projection_type = "ALL"
  }

  # GSI 2 — triage queue queries by status (replaces table.scan())
  global_secondary_index {
    name            = "status-created-index"
    hash_key        = "status"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  # GSI 3 — idempotency check (prevents double submits)
  global_secondary_index {
    name            = "idempotency-key-index"
    hash_key        = "idempotency_key"
    projection_type = "ALL"
  }

  # TTL — auto-expire demo records after 30 days
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = { Name = "${local.name_prefix}-triage" }
}

# ── DynamoDB: Patients ───────────────────────────────────────────────────────

resource "aws_dynamodb_table" "patients" {
  name         = "${local.name_prefix}-patients"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "hospital_id"

  attribute {
    name = "hospital_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = { Name = "${local.name_prefix}-patients" }
}
