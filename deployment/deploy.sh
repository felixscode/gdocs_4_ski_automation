#!/bin/bash
# Deployment script for Google Cloud Function

# Configuration
PROJECT_ID="kursanmeldungen-439011"
FUNCTION_NAME="RegrstrationServiceFunction"
REGION="us-central1"
RUNTIME="python311"  # or python312
ENTRY_POINT="main"
MEMORY="512MB"
TIMEOUT="540s"  # 9 minutes max for email sending
MAX_INSTANCES="10"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Deploying Cloud Function ===${NC}"

# Check if required files exist
required_files=(
    "main.py"
    "requirements.txt"
    "client_secret.json"
    "client_secret_mail.json"
    "mail_setting.yaml"
    "paid.html"
    "registration.html"
    "checklist.pdf"
)

echo "Checking required files..."
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: Missing required file: $file${NC}"
        exit 1
    fi
    echo "  ✓ $file"
done

echo -e "\n${GREEN}All files present. Deploying...${NC}\n"

# Deploy the function
gcloud functions deploy $FUNCTION_NAME \
    --gen2 \
    --runtime=$RUNTIME \
    --region=$REGION \
    --source=. \
    --entry-point=$ENTRY_POINT \
    --trigger-http \
    --allow-unauthenticated \
    --memory=$MEMORY \
    --timeout=$TIMEOUT \
    --max-instances=$MAX_INSTANCES \
    --project=$PROJECT_ID

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}=== Deployment Successful ===${NC}"
    echo -e "\nFunction URL:"
    gcloud functions describe $FUNCTION_NAME \
        --gen2 \
        --region=$REGION \
        --project=$PROJECT_ID \
        --format='value(serviceConfig.uri)'
else
    echo -e "\n${RED}=== Deployment Failed ===${NC}"
    exit 1
fi
