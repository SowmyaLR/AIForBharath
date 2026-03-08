# ════════════════════════════════════════════
#  VaidyaSaarathi — MedGemma SageMaker Infra
#  SageMaker Model + Endpoint ONLY
#  Storage (S3/DynamoDB) is in infra_storage/
# ════════════════════════════════════════════

# ── IAM propagation wait ─────────────────────────────────────────────────────
# SageMaker endpoint creation fails if it starts before IAM role is fully
# propagated globally. The 15s sleep eliminates the race condition.

resource "time_sleep" "iam_propagation" {
  depends_on      = [aws_iam_role.sagemaker_exec]
  create_duration = "15s"
}

# ── SageMaker Model (HuggingFace TGI + MedGemma weights) ────────────────────

resource "aws_sagemaker_model" "medgemma" {
  name               = "${local.name_prefix}-medgemma-model"
  execution_role_arn = aws_iam_role.sagemaker_exec.arn

  depends_on = [time_sleep.iam_propagation]

  primary_container {
    image = local.tgi_image_uri

    environment = {
      HF_MODEL_ID      = var.medgemma_model_id
      HF_TOKEN         = var.hf_token
      SM_NUM_GPUS      = "1"
      MAX_INPUT_LENGTH = "3072"
      MAX_TOTAL_TOKENS = "4096"
    }
  }

  tags = { Name = "${local.name_prefix}-medgemma-model" }
}

# ── Endpoint Configuration ───────────────────────────────────────────────────

resource "aws_sagemaker_endpoint_configuration" "medgemma" {
  name = "${local.name_prefix}-medgemma-epc"

  async_inference_config {
    output_config {
      s3_output_path = "s3://${aws_s3_bucket.async_outputs.bucket}/medgemma-outputs/"
    }
  }

  production_variants {
    variant_name                                      = "primary"
    model_name                                        = aws_sagemaker_model.medgemma.name
    instance_type                                     = var.medgemma_instance_type
    initial_instance_count                            = var.medgemma_initial_instance_count
    container_startup_health_check_timeout_in_seconds = 600
  }

  tags = { Name = "${local.name_prefix}-medgemma-epc" }
}

# ── Real-Time Inference Endpoint ─────────────────────────────────────────────

resource "aws_sagemaker_endpoint" "medgemma" {
  name                 = "${local.name_prefix}-medgemma-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.medgemma.name

  tags = { Name = "${local.name_prefix}-medgemma-endpoint" }
}

# ── S3: Async Inference Outputs ──────────────────────────────────────────────

resource "aws_s3_bucket" "async_outputs" {
  bucket = "${local.name_prefix}-sagemaker-async-${data.aws_caller_identity.current.account_id}"
  tags   = { Name = "${local.name_prefix}-sagemaker-async" }
}

resource "aws_s3_bucket_public_access_block" "async_outputs" {
  bucket                  = aws_s3_bucket.async_outputs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── Auto Scaling: Scale-to-Zero ───────────────────────────────────────────────

resource "aws_appautoscaling_target" "sagemaker_target" {
  min_capacity       = 0
  max_capacity       = 1
  resource_id        = "endpoint/${aws_sagemaker_endpoint.medgemma.name}/variant/primary"
  scalable_dimension = "sagemaker:variant:DesiredInstanceCount"
  service_namespace  = "sagemaker"
}

# Scale OUT policy (starts the instance when a message exists)
resource "aws_appautoscaling_policy" "scale_out" {
  name               = "${local.name_prefix}-medgemma-scale-out"
  resource_id        = aws_appautoscaling_target.sagemaker_target.resource_id
  scalable_dimension = aws_appautoscaling_target.sagemaker_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.sagemaker_target.service_namespace
  policy_type        = "StepScaling"

  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    cooldown                = 300
    metric_aggregation_type = "Average"

    step_adjustment {
      metric_interval_lower_bound = 0
      scaling_adjustment          = 1
    }
  }
}

# Scale IN policy (shuts down after 10 min idle)
resource "aws_appautoscaling_policy" "scale_in" {
  name               = "${local.name_prefix}-medgemma-scale-in"
  resource_id        = aws_appautoscaling_target.sagemaker_target.resource_id
  scalable_dimension = aws_appautoscaling_target.sagemaker_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.sagemaker_target.service_namespace
  policy_type        = "StepScaling"

  step_scaling_policy_configuration {
    adjustment_type         = "ExactCapacity"
    cooldown                = 300
    metric_aggregation_type = "Average"

    step_adjustment {
      metric_interval_upper_bound = 0
      scaling_adjustment          = 0
    }
  }
}

# CloudWatch Alarm for Scale OUT
resource "aws_cloudwatch_metric_alarm" "has_capacity" {
  alarm_name          = "${local.name_prefix}-medgemma-async-has-backlog"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateBacklogSize"
  namespace           = "AWS/SageMaker"
  period              = 60
  statistic           = "Average"
  threshold           = 0
  alarm_actions       = [aws_appautoscaling_policy.scale_out.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    EndpointName = aws_sagemaker_endpoint.medgemma.name
  }
}

# CloudWatch Alarm for Scale IN (10 minutes)
resource "aws_cloudwatch_metric_alarm" "no_capacity" {
  alarm_name          = "${local.name_prefix}-medgemma-async-no-backlog"
  comparison_operator = "LessThanOrEqualToThreshold"
  evaluation_periods  = 10 # 10 periods x 60s = 10 minutes
  metric_name         = "ApproximateBacklogSize"
  namespace           = "AWS/SageMaker"
  period              = 60
  statistic           = "Average"
  threshold           = 0
  alarm_actions       = [aws_appautoscaling_policy.scale_in.arn]
  treat_missing_data  = "breaching"

  dimensions = {
    EndpointName = aws_sagemaker_endpoint.medgemma.name
  }
}

# ── CloudWatch Alarms for Endpoint Health ────────────────────────────────────

resource "aws_cloudwatch_metric_alarm" "endpoint_invocation_errors" {
  alarm_name          = "${local.name_prefix}-medgemma-invocation-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "InvocationModelErrors"
  namespace           = "AWS/SageMaker"
  period              = 60
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "MedGemma endpoint is throwing too many errors"
  treat_missing_data  = "notBreaching"

  dimensions = {
    EndpointName = aws_sagemaker_endpoint.medgemma.name
    VariantName  = "primary"
  }
}

resource "aws_cloudwatch_metric_alarm" "endpoint_latency_high" {
  alarm_name          = "${local.name_prefix}-medgemma-latency-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "ModelLatency"
  namespace           = "AWS/SageMaker"
  period              = 60
  extended_statistic  = "p90"
  threshold           = 10000000 # 10s in microseconds
  alarm_description   = "MedGemma P90 latency exceeds 10 seconds"
  treat_missing_data  = "notBreaching"

  dimensions = {
    EndpointName = aws_sagemaker_endpoint.medgemma.name
    VariantName  = "primary"
  }
}
