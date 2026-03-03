#!/bin/bash
# ════════════════════════════════════════════════════════════════
#  VaidyaSaarathi - Backend Build & Push to ECR (DEMO)
# ════════════════════════════════════════════════════════════════

set -e

# Configuration
AWS_REGION="ap-south-1"
ECR_REPO_NAME="vaidyasaarathi-api"
IMAGE_TAG="demo"
# Dynamically get account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URL="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "🚀 Starting Backend Deployment for AWS..."

# 1. Login to ECR
echo "🔑 Logging in to Amazon ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URL}

# 2. Build the Backend Image (demo mode)
echo "🏗️ Building Backend Docker Image (Tag: ${IMAGE_TAG})..."
docker build --platform linux/amd64 -t ${ECR_REPO_NAME}:${IMAGE_TAG} ./server

# 3. Tag & Push
echo "🏷️ Tagging and Pushing to ECR: ${ECR_URL}/${ECR_REPO_NAME}:${IMAGE_TAG}..."
docker tag ${ECR_REPO_NAME}:${IMAGE_TAG} ${ECR_URL}/${ECR_REPO_NAME}:${IMAGE_TAG}
docker push ${ECR_URL}/${ECR_REPO_NAME}:${IMAGE_TAG}

echo "✅ Successfully Pushed Backend to ECR!"
