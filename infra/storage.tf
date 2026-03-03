# ════════════════════════════════════════════
#  VaidyaSaarathi — Demo Storage Resources
#  S3 (Audio) + DynamoDB (Triage + Patients)
# ════════════════════════════════════════════

# ── S3 Bucket for Audio Recordings ─────────────────────────────────────────

resource "aws_s3_bucket" "audio" {
  bucket = "${local.name_prefix}-audio"

  tags = {
    Name = "${local.name_prefix}-audio"
  }
}

resource "aws_s3_bucket_versioning" "audio" {
  bucket = aws_s3_bucket.audio.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "audio" {
  bucket = aws_s3_bucket.audio.id

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

# ── DynamoDB Table: Triage Records ─────────────────────────────────────────

resource "aws_dynamodb_table" "triage" {
  name         = "${local.name_prefix}-triage"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  # GSI for querying triage records by patient
  global_secondary_index {
    name            = "patient_id-index"
    hash_key        = "patient_id"
    projection_type = "ALL"
  }

  attribute {
    name = "patient_id"
    type = "S"
  }

  # Enable TTL so stale demo records auto-expire after 30 days
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = {
    Name = "${local.name_prefix}-triage"
  }
}

# ── DynamoDB Table: Patients ────────────────────────────────────────────────

resource "aws_dynamodb_table" "patients" {
  name         = "${local.name_prefix}-patients"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "hospital_id"

  attribute {
    name = "hospital_id"
    type = "S"
  }

  tags = {
    Name = "${local.name_prefix}-patients"
  }
}
