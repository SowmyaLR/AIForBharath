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
