# ════════════════════════════════════════════
#  VaidyaSaarathi — SQS Resources
#  triage-jobs queue + DLQ + SNS + Alarms
# ════════════════════════════════════════════

# ── Dead Letter Queue ───────────────────────────────────────────────────────
# Receives messages after 3 failed processing attempts.
# Ops can re-queue from here without data loss.

resource "aws_sqs_queue" "triage_dlq" {
  name                      = "${local.name_prefix}-triage-dlq"
  message_retention_seconds = 86400 # 24 hrs — time for ops intervention

  tags = { Name = "${local.name_prefix}-triage-dlq" }
}

# ── Main Triage Job Queue ───────────────────────────────────────────────────
# Visibility timeout > max inference time (25s) to avoid duplicate processing.

resource "aws_sqs_queue" "triage_jobs" {
  name                       = "${local.name_prefix}-triage-jobs"
  visibility_timeout_seconds = 120   # 2 min — exceeds worst-case inference time
  message_retention_seconds  = 14400 # 4 hrs — ops window to handle stalls

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.triage_dlq.arn
    maxReceiveCount     = 3 # 3 attempts before routing to DLQ
  })

  tags = { Name = "${local.name_prefix}-triage-jobs" }
}

# Allow ECS task role to send messages to this queue
resource "aws_sqs_queue_policy" "triage_jobs" {
  queue_url = aws_sqs_queue.triage_jobs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowECSTaskSend"
      Effect    = "Allow"
      Principal = { AWS = "*" } # Scoped at IAM task role level in infra_be
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.triage_jobs.arn
    }]
  })
}

# ── SNS Topic for Operational Alerts ───────────────────────────────────────

resource "aws_sns_topic" "alerts" {
  name = "${local.name_prefix}-alerts"
  tags = { Name = "${local.name_prefix}-alerts" }
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
  # NOTE: AWS sends a confirmation email — you must click the link to activate
}

# ── CloudWatch Alarm: DLQ Not Empty ────────────────────────────────────────
# Fires immediately when any message lands in the DLQ.
# This means a triage job has permanently failed after 3 retries.

resource "aws_cloudwatch_metric_alarm" "dlq_not_empty" {
  alarm_name          = "${local.name_prefix}-dlq-not-empty"
  alarm_description   = "A triage job permanently failed (DLQ received a message). Check /triage/{id} in DynamoDB for details."
  comparison_operator = "GreaterThanThreshold"
  threshold           = 0
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Sum"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.triage_dlq.name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}

# ── CloudWatch Alarm: Queue Depth Spike ────────────────────────────────────
# Fires if > 10 messages accumulate — indicates Lambda worker is not keeping up.

resource "aws_cloudwatch_metric_alarm" "queue_depth" {
  alarm_name          = "${local.name_prefix}-queue-depth-high"
  alarm_description   = "Triage queue has > 10 pending jobs — Lambda worker may be stalled."
  comparison_operator = "GreaterThanThreshold"
  threshold           = 10
  evaluation_periods  = 2
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Sum"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.triage_jobs.name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}
