# ════════════════════════════════════════════
#  VaidyaSaarathi - MedGemma SageMaker Infra
#  Terraform Outputs
# ════════════════════════════════════════════

output "medgemma_endpoint_name" {
  description = "SageMaker endpoint name — put this in .env.demo as SAGEMAKER_MEDGEMMA_ENDPOINT"
  value       = aws_sagemaker_endpoint.medgemma.name
}

output "medgemma_endpoint_arn" {
  description = "SageMaker endpoint ARN"
  value       = aws_sagemaker_endpoint.medgemma.arn
}

output "sagemaker_execution_role_arn" {
  description = "IAM role ARN used by SageMaker"
  value       = aws_iam_role.sagemaker_exec.arn
}

output "model_artifacts_bucket" {
  description = "S3 bucket for model artifacts and triage audio storage"
  value       = aws_s3_bucket.artifacts.bucket
}
