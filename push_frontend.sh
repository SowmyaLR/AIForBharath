#!/bin/bash
# ════════════════════════════════════════════════════════════════
#  VaidyaSaarathi - Frontend Build & Push to ECR (DEMO)
# ════════════════════════════════════════════════════════════════

set -e

# Configuration
AWS_REGION="ap-south-1"
ECR_REPO_NAME="vaidyasaarathi-client"
IMAGE_TAG="demo"
# Dynamically get account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URL="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "🚀 Starting Frontend Deployment for AWS..."

# 1. Login to ECR
echo "🔑 Logging in to Amazon ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URL}

# 2. Build the Frontend Image
echo "🏗️ Building Frontend Docker Image (Tag: ${IMAGE_TAG})..."
# Pass the production API URL as a build arg
docker build --platform linux/amd64 \
  --build-arg NEXT_PUBLIC_API_URL="http://65.0.60.206:8000" \
  -t ${ECR_REPO_NAME}:${IMAGE_TAG} ./client

# 3. Tag & Push
echo "🏷️ Tagging and Pushing to ECR: ${ECR_URL}/${ECR_REPO_NAME}:${IMAGE_TAG}..."
docker tag ${ECR_REPO_NAME}:${IMAGE_TAG} ${ECR_URL}/${ECR_REPO_NAME}:${IMAGE_TAG}
docker push ${ECR_URL}/${ECR_REPO_NAME}:${IMAGE_TAG}

echo "✅ Successfully Pushed Frontend to ECR!"
