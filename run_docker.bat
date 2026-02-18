@echo off
setlocal enabledelayedexpansion

echo Running Cloud Archaeologist in Docker
echo =====================================

REM Check if Docker is installed
where docker >nul 2>nul
if errorlevel 1 (
    echo Error: Docker is not installed or not in PATH
    exit /b 1
)

REM Check if image exists
docker images cloud-archaeologist --format "table {{.Repository}}:{{.Tag}}" | findstr cloud-archaeologist >nul
if errorlevel 1 (
    echo Image not found. Building Docker image...
    call build_docker.bat
)

REM Create reports directory if it doesn't exist
if not exist "reports" mkdir reports

REM Set default values
set "FORMAT=txt"
set "QUIET_MODE="
set "REGION="
set "PROFILE="
set "REMOVE_AFTER_RUN="
set "INTERACTIVE_MODE="

REM Parse command line arguments
:parse_args
if "%~1"=="" goto execute
if "%~1"=="-h" goto show_help
if "%~1"=="--help" goto show_help
if "%~1"=="-f" set "FORMAT=%~2" && shift && goto next_arg
if "%~1"=="--format" set "FORMAT=%~2" && shift && goto next_arg
if "%~1"=="-q" set "QUIET_MODE=--quiet" && goto next_arg
if "%~1"=="--quiet" set "QUIET_MODE=--quiet" && goto next_arg
if "%~1"=="-r" set "REGION=%~2" && shift && goto next_arg
if "%~1"=="--region" set "REGION=%~2" && shift && goto next_arg
if "%~1"=="-p" set "PROFILE=%~2" && shift && goto next_arg
if "%~1"=="--profile" set "PROFILE=%~2" && shift && goto next_arg
if "%~1"=="-i" set "INTERACTIVE_MODE=-it" && goto next_arg
if "%~1"=="--interactive" set "INTERACTIVE_MODE=-it" && goto next_arg
if "%~1"=="--rm" set "REMOVE_AFTER_RUN=--rm" && goto next_arg

:next_arg
shift
goto parse_args

:execute
set "CMD_ARGS=run "
if defined REMOVE_AFTER_RUN set "CMD_ARGS=!CMD_ARGS!%REMOVE_AFTER_RUN% "
if defined INTERACTIVE_MODE (set "CMD_ARGS=!CMD_ARGS!%INTERACTIVE_MODE%") else (set "CMD_ARGS=!CMD_ARGS!-t")
if defined REGION set "CMD_ARGS=!CMD_ARGS! -e AWS_DEFAULT_REGION=%REGION%"
set "CMD_ARGS=!CMD_ARGS! -v %cd%\reports:/app/reports -v %USERPROFILE%\.aws:/home/appuser/.aws:ro"
set "CMD_ARGS=!CMD_ARGS! --name cloud-archaeologist_!time:~6,2!!time:~9,2!!time:~12,2!"
set "CMD_ARGS=!CMD_ARGS! cloud-archaeologist:latest python cloud_archaeologist.py --format %FORMAT%"

if defined QUIET_MODE set "CMD_ARGS=!CMD_ARGS! %QUIET_MODE%"
if defined REGION set "CMD_ARGS=!CMD_ARGS! --region %REGION%"
if defined PROFILE set "CMD_ARGS=!CMD_ARGS! --profile %PROFILE%"

echo Executing: docker !CMD_ARGS!
docker !CMD_ARGS!

if !errorlevel! equ 0 (
    echo.
    echo Cloud Archaeologist execution completed!
    echo Reports saved to: %cd%\reports
    if not defined REMOVE_AFTER_RUN (
        echo To view container logs: docker logs cloud-archaeologist_!time:~6,2!!time:~9,2!!time:~12,2!
        echo To enter the container: docker exec -it cloud-archaeologist_!time:~6,2!!time:~9,2!!time:~12,2! /bin/bash
    )
) else (
    echo Failed to run Cloud Archaeologist container
    exit /b 1
)
goto end

:show_help
echo Usage: %~n0 [OPTIONS]
echo Options:
echo   -h, --help              Show this help message
echo   -f, --format FORMAT     Output format (txt, csv, json) - default: txt
echo   -q, --quiet             Run in quiet mode
echo   -r, --region REGION     AWS region to scan - default: all regions
echo   -p, --profile PROFILE   AWS profile name - default: default
echo   -i, --interactive       Run in interactive mode
echo   --rm                    Remove container after run - default: false
echo.
echo Examples:
echo   %~n0                                      ^& Rem Run with default options
echo   %~n0 -f json                              ^& Rem Generate JSON report
echo   %~n0 -q -r us-west-2                      ^& Rem Quiet mode, specific region
echo   %~n0 -f csv --rm                          ^& Rem Generate CSV and remove container
echo   %~n0 -i                                   ^& Rem Interactive mode
goto end

:end