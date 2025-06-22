#!/bin/bash

# Exit on any error
set -e

# Configuration
IMAGE_NAME="decipher-backend"
DOCKER_REGISTRY="mtwn105"
VERSION=$(git describe --tags --always)

# Build the Docker image
echo "Building Docker image..."
docker build -t $IMAGE_NAME:$VERSION .

# Tag the image with latest
docker tag $IMAGE_NAME:$VERSION $DOCKER_REGISTRY/$IMAGE_NAME:latest
docker tag $IMAGE_NAME:$VERSION $DOCKER_REGISTRY/$IMAGE_NAME:$VERSION

# Push the images
echo "Pushing Docker images..."
docker push $DOCKER_REGISTRY/$IMAGE_NAME:latest
docker push $DOCKER_REGISTRY/$IMAGE_NAME:$VERSION

echo "Successfully built and pushed version $VERSION"
