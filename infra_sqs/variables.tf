# ════════════════════════════════════════════
#  VaidyaSaarathi — SQS Variables
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

variable "alert_email" {
  description = "Email address to receive SNS alert notifications"
  type        = string
  # Set in terraform.tfvars — e.g. ops@yourdomain.com
}
