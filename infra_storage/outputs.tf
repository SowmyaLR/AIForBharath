# ════════════════════════════════════════════
#  VaidyaSaarathi — Storage Outputs
#  Consumed by infra_be via terraform_remote_state
# ════════════════════════════════════════════

output "audio_bucket_name" {
  description = "S3 bucket for triage audio — set as AUDIO_S3_BUCKET in ECS env"
  value       = aws_s3_bucket.audio.bucket
}

output "audio_bucket_arn" {
  description = "ARN of the audio S3 bucket (used in IAM policies)"
  value       = aws_s3_bucket.audio.arn
}

output "fhir_bucket_name" {
  description = "S3 bucket for FHIR bundles — set as FHIR_S3_BUCKET in ECS env"
  value       = aws_s3_bucket.fhir.bucket
}

output "fhir_bucket_arn" {
  description = "ARN of the FHIR S3 bucket (used in IAM policies)"
  value       = aws_s3_bucket.fhir.arn
}

output "triage_table_name" {
  description = "DynamoDB triage table — set as DYNAMODB_TRIAGE_TABLE in ECS env"
  value       = aws_dynamodb_table.triage.name
}

output "triage_table_arn" {
  description = "ARN of the triage table (used in IAM policies)"
  value       = aws_dynamodb_table.triage.arn
}

output "patients_table_name" {
  description = "DynamoDB patients table — set as DYNAMODB_PATIENTS_TABLE in ECS env"
  value       = aws_dynamodb_table.patients.name
}

output "patients_table_arn" {
  description = "ARN of the patients table (used in IAM policies)"
  value       = aws_dynamodb_table.patients.arn
}
