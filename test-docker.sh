#!/bin/bash
# Test script for watermark detector Docker image

set -e

IMAGE_NAME="watermark-detector:test"

echo "=========================================="
echo "Watermark Detector Docker Image Test"
echo "=========================================="

# Build the Docker image
echo ""
echo "[1/4] Building Docker image..."
docker build -f Dockerfile.watermark -t "$IMAGE_NAME" .

echo ""
echo "[2/4] Checking image size..."
IMAGE_SIZE=$(docker images "$IMAGE_NAME" --format "{{.Size}}")
echo "Image size: $IMAGE_SIZE"

echo ""
echo "[3/4] Testing image with --help..."
docker run --rm "$IMAGE_NAME" --help || echo "Note: Script may not have --help option"

echo ""
echo "[4/4] Testing with sample image (if available)..."
if [ -f "test.jpg" ] || [ -f "test.png" ]; then
    echo "Found test image, running detection..."
    docker run --rm -v "$(pwd):/workspace" "$IMAGE_NAME" test.* || true
else
    echo "No test image found. To test with an image:"
    echo "  docker run --rm -v \"\$(pwd):/workspace\" $IMAGE_NAME your-image.jpg"
fi

echo ""
echo "=========================================="
echo "✅ Docker image built successfully!"
echo "=========================================="
echo ""
echo "Usage:"
echo "  docker run --rm -v \"\$(pwd):/workspace\" $IMAGE_NAME image.jpg"
echo ""
echo "To push to registry:"
echo "  docker tag $IMAGE_NAME ghcr.io/YOUR_USERNAME/watermark-detector:latest"
echo "  docker push ghcr.io/YOUR_USERNAME/watermark-detector:latest"
echo ""
