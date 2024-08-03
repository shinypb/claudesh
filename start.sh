#!/bin/bash
set -euo pipefail

# Get the top-level directory of the git repository
TOP_LEVEL_DIR=$(git rev-parse --show-toplevel)

# Get the base name of the top-level directory
DIR_NAME=$(basename "${TOP_LEVEL_DIR}")

# Name of the Docker image and container
IMAGE_NAME="${DIR_NAME}_image"
CONTAINER_NAME="${DIR_NAME}"

# Check if the container already exists
CONTAINER_EXISTS=$(docker ps -a --filter "name=^/${CONTAINER_NAME}$" --format '{{.Names}}')

if [ "$CONTAINER_EXISTS" == "$CONTAINER_NAME" ]; then
  docker stop "${CONTAINER_NAME}"
  docker rm "${CONTAINER_NAME}"
fi

# Build the Docker image if not already exists or needs update
echo "Building Docker image ${IMAGE_NAME}"
docker build -t "${IMAGE_NAME}" "${TOP_LEVEL_DIR}"

# Run the Docker container
echo "Running new container ${CONTAINER_NAME}"
docker run --name "${CONTAINER_NAME}" --env-file .env --interactive -p 5980:5980 -v "${TOP_LEVEL_DIR}/app:/app" -v "${TOP_LEVEL_DIR}/task:/task" "${IMAGE_NAME}" "$@"
