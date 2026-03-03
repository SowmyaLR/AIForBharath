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

output "audio_bucket_name" {
  description = "S3 bucket for triage audio recordings — set as AUDIO_S3_BUCKET in .env.demo"
  value       = aws_s3_bucket.audio.bucket
}

output "triage_table_name" {
  description = "DynamoDB triage table name — set as DYNAMODB_TRIAGE_TABLE in .env.demo"
  value       = aws_dynamodb_table.triage.name
}

output "patients_table_name" {
  description = "DynamoDB patients table name — set as DYNAMODB_PATIENTS_TABLE in .env.demo"
  value       = aws_dynamodb_table.patients.name
}

output "ecs_task_role_arn" {
  description = "IAM role ARN for ECS task (FastAPI server) — set in ECS task definition"
  value       = aws_iam_role.ecs_task.arn
}
