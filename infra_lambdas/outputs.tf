# ════════════════════════════════════════════
#  VaidyaSaarathi — Lambda Outputs
# ════════════════════════════════════════════

output "ping_lambda_name" {
  description = "Warm-ping Lambda function name"
  value       = aws_lambda_function.ping_medgemma.function_name
}

output "lifecycle_lambda_name" {
  description = "Endpoint lifecycle Lambda function name"
  value       = aws_lambda_function.endpoint_lifecycle.function_name
}

output "lambda_exec_role_arn" {
  description = "IAM role ARN shared by both Lambdas"
  value       = aws_iam_role.lambda_exec.arn
}
