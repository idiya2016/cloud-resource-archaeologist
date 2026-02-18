#!/bin/bash

# Cloud Archaeologist - Docker Run Script
# This script runs the Cloud Archaeologist container with various options

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
CONTAINER_NAME="cloud-archaeologist"
IMAGE_NAME="cloud-archaeologist:latest"
REPORT_DIR="./reports"
AWS_PROFILE="default"

# Function to display usage
usage() {
    echo -e "${BLUE}Usage:${NC} $0 [OPTIONS]"
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -f, --format FORMAT     Output format (txt, csv, json) - default: txt"
    echo "  -q, --quiet             Run in quiet mode"
    echo "  -r, --region REGION     AWS region to scan - default: all regions"
    echo "  -p, --profile PROFILE   AWS profile name - default: default"
    echo "  -i, --interactive       Run in interactive mode"
    echo "  --rm                    Remove container after run - default: false"
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo "  $0                                      # Run with default options"
    echo "  $0 -f json                              # Generate JSON report"
    echo "  $0 -q -r us-west-2                      # Quiet mode, specific region"
    echo "  $0 -f csv --rm                          # Generate CSV and remove container"
    echo "  $0 -i                                   # Interactive mode"
    echo ""
}

# Parse command line arguments
REMOVE_AFTER_RUN=false
INTERACTIVE_MODE=false
FORMAT="txt"
QUIET_MODE=false
REGION=""
PROFILE=""

while [[ $# -gt 0 ]]; do
    case $F in
        -h|--help)
            usage
            exit 0
            ;;
        -f|--format)
            FORMAT="$2"
            shift 2
            ;;
        -q|--quiet)
            QUIET_MODE=true
            shift
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -p|--profile)
            PROFILE="$2"
            shift 2
            ;;
        -i|--interactive)
            INTERACTIVE_MODE=true
            shift
            ;;
        --rm)
            REMOVE_AFTER_RUN=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}" >&2
            usage
            exit 1
            ;;
    esac
done

echo -e "${GREEN}Running Cloud Archaeologist in Docker${NC}"
echo "======================================="

# Check if Docker is installed
if ! [ -x "$(command -v docker)" ]; then
  echo -e "${RED}Error: Docker is not installed or not in PATH${NC}" >&2
  exit 1
fi

# Check if image exists
if ! docker images | grep -q cloud-archaeologist; then
  echo -e "${YELLOW}Image not found. Building Docker image...${NC}"
  ./build_docker.sh
fi

# Create reports directory if it doesn't exist
mkdir -p "$REPORT_DIR"

# Build docker run command
CMD_ARGS="run"
if [ "$REMOVE_AFTER_RUN" = true ]; then
    CMD_ARGS="$CMD_ARGS --rm"
fi

if [ "$INTERACTIVE_MODE" = true ]; then
    CMD_ARGS="$CMD_ARGS -it"
else
    CMD_ARGS="$CMD_ARGS -t"
fi

# Set environment variables
CMD_ARGS="$CMD_ARGS -e AWS_DEFAULT_REGION=${REGION:-us-east-1}"

# Mount volumes
CMD_ARGS="$CMD_ARGS -v $(pwd)/reports:/app/reports"
CMD_ARGS="$CMD_ARGS -v ~/.aws:/home/appuser/.aws:ro"

# Set container name
CMD_ARGS="$CMD_ARGS --name ${CONTAINER_NAME}_$(date +%s)"

# Set the image name
CMD_ARGS="$CMD_ARGS $IMAGE_NAME"

# Build the command arguments
RUN_CMD="python cloud_archaeologist.py"
if [ -n "$FORMAT" ]; then
    RUN_CMD="$RUN_CMD --format $FORMAT"
fi

if [ "$QUIET_MODE" = true ]; then
    RUN_CMD="$RUN_CMD --quiet"
fi

if [ -n "$REGION" ]; then
    RUN_CMD="$RUN_CMD --region $REGION"
fi

if [ -n "$PROFILE" ]; then
    RUN_CMD="$RUN_CMD --profile $PROFILE"
fi

CMD_ARGS="$CMD_ARGS $RUN_CMD"

echo -e "${YELLOW}Executing: docker $CMD_ARGS${NC}"
echo ""

# Execute the docker run command
eval "docker $CMD_ARGS"

echo -e "\n${GREEN}Cloud Archaeologist execution completed!${NC}"
echo -e "${GREEN}Reports saved to: $(pwd)/reports${NC}"

if [ "$REMOVE_AFTER_RUN" = false ]; then
    echo -e "${BLUE}To view container logs: docker logs ${CONTAINER_NAME}_<timestamp>${NC}"
    echo -e "${BLUE}To enter the container: docker exec -it ${CONTAINER_NAME}_<timestamp> /bin/bash${NC}"
fi