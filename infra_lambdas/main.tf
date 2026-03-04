# ════════════════════════════════════════════
#  VaidyaSaarathi — Lambda Resources
#  1. ping_medgemma  — warm-ping every 8 min
#  2. endpoint_lifecycle — start/stop schedule
# ════════════════════════════════════════════

data "aws_caller_identity" "current" {}

# ── IAM Role for both Lambdas ───────────────────────────────────────────────

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_exec" {
  name               = "${local.name_prefix}-lambda-exec-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

# Basic logging
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Scoped SageMaker permissions — invoke endpoint (ping) + create/delete endpoint (lifecycle)
resource "aws_iam_role_policy" "lambda_sagemaker" {
  name = "sagemaker-access"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "InvokeEndpoint"
        Effect = "Allow"
        Action = ["sagemaker:InvokeEndpoint"]
        Resource = [
          "arn:aws:sagemaker:${var.aws_region}:${data.aws_caller_identity.current.account_id}:endpoint/${var.medgemma_endpoint_name}"
        ]
      },
      {
        Sid    = "ManageEndpointLifecycle"
        Effect = "Allow"
        Action = [
          "sagemaker:CreateEndpoint",
          "sagemaker:DeleteEndpoint",
          "sagemaker:DescribeEndpoint"
        ]
        Resource = [
          "arn:aws:sagemaker:${var.aws_region}:${data.aws_caller_identity.current.account_id}:endpoint/${var.medgemma_endpoint_name}",
          "arn:aws:sagemaker:${var.aws_region}:${data.aws_caller_identity.current.account_id}:endpoint-config/${var.medgemma_endpoint_config}"
        ]
      }
    ]
  })
}

# ── Lambda 1: ping_medgemma ─────────────────────────────────────────────────

data "archive_file" "ping" {
  type        = "zip"
  source_file = "${path.module}/lambda/ping_medgemma.py"
  output_path = "${path.module}/lambda/ping_medgemma.zip"
}

resource "aws_lambda_function" "ping_medgemma" {
  function_name    = "${local.name_prefix}-ping-medgemma"
  description      = "Warm-ping for MedGemma SageMaker endpoint — keeps GPU VRAM loaded"
  runtime          = "python3.12"
  handler          = "ping_medgemma.handler"
  role             = aws_iam_role.lambda_exec.arn
  filename         = data.archive_file.ping.output_path
  source_code_hash = data.archive_file.ping.output_base64sha256
  timeout          = 30

  environment {
    variables = {
      MEDGEMMA_ENDPOINT = var.medgemma_endpoint_name
      AWS_REGION_NAME   = var.aws_region
    }
  }
}

resource "aws_cloudwatch_log_group" "ping" {
  name              = "/aws/lambda/${aws_lambda_function.ping_medgemma.function_name}"
  retention_in_days = 7
}

# EventBridge rule: every 8 min during clinic hours (02:00–15:00 UTC = 07:30–20:30 IST)
resource "aws_cloudwatch_event_rule" "warmup" {
  name                = "${local.name_prefix}-warmup"
  description         = "Triggers MedGemma warm-ping every 8 minutes during clinic hours"
  schedule_expression = "rate(8 minutes)"
}

resource "aws_cloudwatch_event_target" "warmup" {
  rule      = aws_cloudwatch_event_rule.warmup.name
  target_id = "ping_medgemma"
  arn       = aws_lambda_function.ping_medgemma.arn
}

resource "aws_lambda_permission" "allow_eventbridge_ping" {
  statement_id  = "AllowEventBridgePing"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ping_medgemma.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.warmup.arn
}

# ── Lambda 2: endpoint_lifecycle ────────────────────────────────────────────

data "archive_file" "lifecycle" {
  type        = "zip"
  source_file = "${path.module}/lambda/endpoint_lifecycle.py"
  output_path = "${path.module}/lambda/endpoint_lifecycle.zip"
}

resource "aws_lambda_function" "endpoint_lifecycle" {
  function_name    = "${local.name_prefix}-endpoint-lifecycle"
  description      = "Starts MedGemma endpoint at 07:50 IST, stops at 20:00 IST"
  runtime          = "python3.12"
  handler          = "endpoint_lifecycle.handler"
  role             = aws_iam_role.lambda_exec.arn
  filename         = data.archive_file.lifecycle.output_path
  source_code_hash = data.archive_file.lifecycle.output_base64sha256
  timeout          = 60 # endpoint creation can take up to 30s to respond

  environment {
    variables = {
      MEDGEMMA_ENDPOINT        = var.medgemma_endpoint_name
      MEDGEMMA_ENDPOINT_CONFIG = var.medgemma_endpoint_config
      AWS_REGION_NAME          = var.aws_region
    }
  }
}

resource "aws_cloudwatch_log_group" "lifecycle" {
  name              = "/aws/lambda/${aws_lambda_function.endpoint_lifecycle.function_name}"
  retention_in_days = 7
}

# Start: cron(20 2 * * ? *) = 02:20 UTC = 07:50 IST
resource "aws_cloudwatch_event_rule" "start_endpoint" {
  name                = "${local.name_prefix}-start-endpoint"
  description         = "Starts MedGemma endpoint at 07:50 IST (10 min before clinic opens)"
  schedule_expression = "cron(20 2 * * ? *)"
}

resource "aws_cloudwatch_event_target" "start_endpoint" {
  rule      = aws_cloudwatch_event_rule.start_endpoint.name
  target_id = "endpoint_lifecycle_start"
  arn       = aws_lambda_function.endpoint_lifecycle.arn
  input     = jsonencode({ action = "start" })
}

resource "aws_lambda_permission" "allow_eventbridge_start" {
  statement_id  = "AllowEventBridgeStart"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.endpoint_lifecycle.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.start_endpoint.arn
}

# Stop: cron(30 14 * * ? *) = 14:30 UTC = 20:00 IST
resource "aws_cloudwatch_event_rule" "stop_endpoint" {
  name                = "${local.name_prefix}-stop-endpoint"
  description         = "Stops MedGemma endpoint at 20:00 IST to eliminate overnight idle GPU cost"
  schedule_expression = "cron(30 14 * * ? *)"
}

resource "aws_cloudwatch_event_target" "stop_endpoint" {
  rule      = aws_cloudwatch_event_rule.stop_endpoint.name
  target_id = "endpoint_lifecycle_stop"
  arn       = aws_lambda_function.endpoint_lifecycle.arn
  input     = jsonencode({ action = "stop" })
}

resource "aws_lambda_permission" "allow_eventbridge_stop" {
  statement_id  = "AllowEventBridgeStop"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.endpoint_lifecycle.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.stop_endpoint.arn
}
