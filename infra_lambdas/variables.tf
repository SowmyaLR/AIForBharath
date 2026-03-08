# ════════════════════════════════════════════
#  VaidyaSaarathi — Lambda Variables
# ════════════════════════════════════════════

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "project" {
  description = "Project name prefix"
  type        = string
  default     = "vaidyasaarathi"
}

variable "environment" {
  description = "Environment name (demo, prod)"
  type        = string
  default     = "demo"
}

variable "medgemma_endpoint_name" {
  description = "SageMaker endpoint name from infra/ — do not change"
  type        = string
  # Copy from: cd infra && terraform output medgemma_endpoint_name
}

variable "medgemma_endpoint_config" {
  description = "SageMaker endpoint config name from infra/ — do not change"
  type        = string
  # Copy from: cd infra && terraform output medgemma_endpoint_config_name (or check AWS console)
}

variable "alert_sns_topic_arn" {
  description = "SNS topic ARN from infra_sqs — copy from infra_sqs outputs"
  type        = string
  # Copy from: cd infra_sqs && terraform output sns_topic_arn
}
