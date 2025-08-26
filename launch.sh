#!/bin/bash
set -e

IMAGE_NAME="box_office"
IMAGE_TAG="latest"

# -----------------------------
# Step 1: Build Docker Image
# -----------------------------
echo "🚀 Building Docker image: $IMAGE_NAME:$IMAGE_TAG ..."
docker build -t $IMAGE_NAME:$IMAGE_TAG .

# -----------------------------
# Step 2: Run docker-compose
# -----------------------------
echo "📦 Starting services with docker compose ..."
docker compose -f docker-compose.yaml up -d
