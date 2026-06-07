# Build and run the Docker-based PoC runner
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Write-Host "Building Docker image..."
docker build -t ai_tester_runner $root
Write-Host "Running tests inside container (with PYTHONPATH=/app)..."
docker run --rm -e "PYTHONPATH=/app" -v "${root}:/app" ai_tester_runner
