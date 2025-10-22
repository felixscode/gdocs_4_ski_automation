# Google Cloud Function Deployment Guide

## Prerequisites

1. **Google Cloud CLI** installed and authenticated
   ```bash
   gcloud auth login
   gcloud config set project kursanmeldungen-439011
   ```

2. **Required files** in deployment directory:
   - `main.py` (cloud function entry point)
   - `requirements.txt` (dependencies)
   - `client_secret.json` (Google Sheets API credentials)
   - `client_secret_mail.json` (Gmail OAuth credentials)
   - `mail_setting.yaml` (email configuration)
   - `paid.html` (payment confirmation email template)
   - `registration.html` (registration confirmation email template)
   - `checklist.pdf` (attachment for registration emails)

## Deployment Steps

### Option 1: Using the deployment script (recommended)

```bash
chmod +x deploy.sh
./deploy.sh
```

### Option 2: Manual deployment

```bash
gcloud functions deploy RegrstrationServiceFunction \
    --gen2 \
    --runtime=python311 \
    --region=us-central1 \
    --source=. \
    --entry-point=main \
    --trigger-http \
    --allow-unauthenticated \
    --memory=512MB \
    --timeout=540s \
    --max-instances=10 \
    --project=kursanmeldungen-439011
```

## Verification

After deployment, test the function:

```bash
# Get function URL
FUNCTION_URL=$(gcloud functions describe RegrstrationServiceFunction \
    --gen2 \
    --region=us-central1 \
    --format='value(serviceConfig.uri)')

# Test with curl
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" $FUNCTION_URL
```

## AppScript Setup

1. Open your Google Sheet
2. Go to **Extensions > Apps Script**
3. Replace the code with contents from `appscript.js`
4. Update `CLOUD_FUNCTION_URL` if your function URL differs
5. Save and reload the spreadsheet
6. You should see "🎿 Kursanmeldung" menu

## Troubleshooting

### Check logs
```bash
gcloud functions logs read RegrstrationServiceFunction \
    --region=us-central1 \
    --limit=50
```

### Common issues

1. **Missing files error**: Ensure all required files are in deployment directory
2. **Authentication error**: Verify OAuth tokens are valid
3. **Timeout**: Increase `--timeout` if processing takes longer
4. **Memory error**: Increase `--memory` parameter

### Update function after code changes

If you only updated the GitHub repo:
```bash
# Cloud Function will pull latest code on next cold start
# Or trigger redeployment:
./deploy.sh
```

## Security Notes

- Function uses `--allow-unauthenticated` but checks Bearer token in code
- For production, consider using Cloud IAM for authentication
- Keep credential files secure and never commit to git
- Rotate OAuth tokens regularly

## Monitoring

View function metrics in Google Cloud Console:
https://console.cloud.google.com/functions/details/us-central1/RegrstrationServiceFunction?project=kursanmeldungen-439011

## Cost Optimization

- Current settings allow max 10 concurrent instances
- 512MB memory should be sufficient for most operations
- Timeout set to 9 minutes to handle slow email sending
- Consider Cloud Scheduler for automatic periodic execution instead of manual triggers
