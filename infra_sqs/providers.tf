# ════════════════════════════════════════════
#  VaidyaSaarathi — SQS Infrastructure
#  triage-jobs queue + DLQ + SNS Alerts
# ════════════════════════════════════════════

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
      Module      = "sqs"
    }
  }
}

locals {
  name_prefix = "${var.project}-${var.environment}-v2"
}
