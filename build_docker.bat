@echo off
setlocal

echo Building Cloud Archaeologist Docker Image
echo =========================================

REM Check if Docker is installed
where docker >nul 2>nul
if errorlevel 1 (
    echo Error: Docker is not installed or not in PATH
    exit /b 1
)

REM Check if we're in the correct directory
if not exist "Dockerfile" (
    echo Error: Dockerfile not found. Please run this script from the project root directory.
    exit /b 1
)

if not exist "requirements.txt" (
    echo Error: requirements.txt not found. Please run this script from the project root directory.
    exit /b 1
)

if not exist "cloud_archaeologist.py" (
    echo Error: cloud_archaeologist.py not found. Please run this script from the project root directory.
    exit /b 1
)

echo Building Docker image...
docker build -t cloud-archaeologist:latest .

if %errorlevel% equ 0 (
    echo Successfully built Cloud Archaeologist Docker image!
    echo Image: cloud-archaeologist:latest
    docker images cloud-archaeologist:latest
    echo.
    echo To run the container, use: docker run -it cloud-archaeologist:latest
    echo Or use the run script: run_docker.bat
) else (
    echo Failed to build Docker image
    exit /b 1
)