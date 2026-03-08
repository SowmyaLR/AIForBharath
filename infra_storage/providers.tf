# ════════════════════════════════════════════
#  VaidyaSaarathi — Storage Infrastructure
#  S3 (Audio + FHIR) + DynamoDB (Triage + Patients)
# ════════════════════════════════════════════

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  # Local backend (default) — state file readable by sibling modules
  # via terraform_remote_state { backend = "local" }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
      Module      = "storage"
    }
  }
}

locals {
  name_prefix = "${var.project}-${var.environment}-v2"
}

data "aws_caller_identity" "current" {}
