#!/bin/bash

# Cloud Archaeologist - Docker Build Script
# This script builds the Docker image for Cloud Archaeologist

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building Cloud Archaeologist Docker Image${NC}"
echo "========================================="

# Check if Docker is installed
if ! [ -x "$(command -v docker)" ]; then
  echo -e "${RED}Error: Docker is not installed or not in PATH${NC}" >&2
  exit 1
fi

# Check if we're in the correct directory
if [ ! -f "Dockerfile" ] || [ ! -f "requirements.txt" ] || [ ! -f "cloud_archaeologist.py" ]; then
  echo -e "${RED}Error: Required files not found. Please run this script from the project root directory.${NC}" >&2
  exit 1
fi

# Build the Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t cloud-archaeologist:latest .

if [ $? -eq 0 ]; then
  echo -e "${GREEN}Successfully built Cloud Archaeologist Docker image!${NC}"
  echo -e "${GREEN}Image: cloud-archaeologist:latest${NC}"
  
  # Show image info
  echo -e "\n${YELLOW}Image Information:${NC}"
  docker images cloud-archaeologist:latest
  
  echo -e "\n${GREEN}To run the container, use:${NC}"
  echo -e "${GREEN}  docker run -it cloud-archaeologist:latest${NC}"
  echo -e "${GREEN}Or use the run script: ./run_docker.sh${NC}"
else
  echo -e "${RED}Failed to build Docker image${NC}" >&2
  exit 1
fi