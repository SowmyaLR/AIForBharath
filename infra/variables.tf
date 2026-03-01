# ════════════════════════════════════════════
#  VaidyaSaarathi - MedGemma SageMaker Infra
#  Terraform Variables
# ════════════════════════════════════════════

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Environment name (demo, prod)"
  type        = string
  default     = "demo"
}

variable "project" {
  description = "Project name prefix for all resources"
  type        = string
  default     = "vaidyasaarathi"
}

variable "medgemma_model_id" {
  description = "HuggingFace model ID for MedGemma"
  type        = string
  default     = "alibayram/medgemma"
}

variable "medgemma_instance_type" {
  description = "SageMaker instance type for MedGemma endpoint"
  type        = string
  default     = "ml.g4dn.xlarge" # 1x T4 GPU ~$0.52/hr
}

variable "medgemma_initial_instance_count" {
  description = "Number of initial instances for the endpoint"
  type        = number
  default     = 1
}

variable "tgi_image_version" {
  description = "HuggingFace TGI DLC image version"
  type        = string
  default     = "1.4.2"
}

variable "hf_token" {
  description = "HuggingFace API token for gated model access"
  type        = string
  sensitive   = true
}
