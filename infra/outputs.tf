# ════════════════════════════════════════════
#  VaidyaSaarathi — MedGemma SageMaker Outputs
#  S3, DynamoDB outputs are in infra_storage/
# ════════════════════════════════════════════

output "medgemma_endpoint_name" {
  description = "SageMaker endpoint name — set as SAGEMAKER_MEDGEMMA_ENDPOINT in your env"
  value       = aws_sagemaker_endpoint.medgemma.name
}

output "medgemma_endpoint_arn" {
  description = "SageMaker endpoint ARN"
  value       = aws_sagemaker_endpoint.medgemma.arn
}

output "medgemma_endpoint_config_name" {
  description = "Endpoint config name — needed for infra_lambdas endpoint_lifecycle Lambda"
  value       = aws_sagemaker_endpoint_configuration.medgemma.name
}

output "sagemaker_execution_role_arn" {
  description = "IAM role ARN used by SageMaker"
  value       = aws_iam_role.sagemaker_exec.arn
}

output "medgemma_async_bucket" {
  description = "S3 bucket for SageMaker Async inputs/outputs"
  value       = aws_s3_bucket.async_outputs.bucket
}
