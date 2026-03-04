# ════════════════════════════════════════════
#  VaidyaSaarathi — SQS Outputs
#  Consumed by infra_be via terraform_remote_state
# ════════════════════════════════════════════

output "queue_url" {
  description = "triage-jobs SQS queue URL — set as SQS_TRIAGE_QUEUE_URL in ECS env"
  value       = aws_sqs_queue.triage_jobs.url
}

output "queue_arn" {
  description = "triage-jobs SQS queue ARN — used in IAM scoped policy in infra_be"
  value       = aws_sqs_queue.triage_jobs.arn
}

output "dlq_arn" {
  description = "DLQ ARN — used in CloudWatch alarm dimensions"
  value       = aws_sqs_queue.triage_dlq.arn
}

output "dlq_url" {
  description = "DLQ URL — for ops re-queuing failed messages"
  value       = aws_sqs_queue.triage_dlq.url
}

output "sns_topic_arn" {
  description = "SNS alerts topic ARN — used in infra_lambdas for failure notifications"
  value       = aws_sns_topic.alerts.arn
}
