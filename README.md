# gdocs_4_ski_automation

Automation tool for managing ski course registrations through Google Sheets integration.

## Overview

This project automates the workflow for ski course registration management by:
- Reading registration data from Google Sheets
- Processing registrations and calculating pricing
- Sending automated email notifications (registration confirmations and payment notifications)
- Updating Google Sheets with processed data

**Note:** This is an alpha-stage project developed for a specific use case. The domain logic could benefit from better encapsulation. Feel free to use or adapt any code for your own purposes.

## Features

- **Google Sheets Integration**: Reads from and writes to Google Sheets for registration management
- **Automated Email Notifications**: Sends customized HTML emails using Jinja2 templates
- **Registration Processing**: Handles registration data with custom business logic
- **Price Calculation**: Automated pricing based on registration details
- **Cloud Function Ready**: Designed to run as a Google Cloud Function triggered via AppScript HTTP requests

## Requirements

- Python >= 3.11
- OAuth 2.0 credentials for Google API access (both desktop and service account)
- Gmail/SMTP credentials for sending emails

## Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/felixscode/gdocs_4_ski_automation.git
   cd gdocs_4_ski_automation
   ```

2. Install dependencies:
   ```sh
   pip install -e .
   ```

   Or using uv:
   ```sh
   uv pip install -e .
   ```

## Configuration

1. **Google API Credentials**:
   - Obtain OAuth 2.0 client secrets from Google Cloud Console
   - Place `client_secret.json` in `data/dependencies/`

2. **Email Credentials**:
   - Set up mail service credentials
   - Place `client_secret_mail.json` in `data/dependencies/`
   - Configure `mail_setting.yaml` with your mail settings

3. **Email Templates**:
   - Create HTML templates for registration and payment emails
   - Place templates in `data/mails/` directory
   - Attach any required PDFs (e.g., checklist) in the same directory

4. **Sheet IDs**:
   - Update the `sheet_ids` dictionary in `service.py` with your Google Sheet IDs:
     - `settings`: Settings configuration sheet
     - `registrations`: Main registrations sheet
     - `db`: Database sheet

## Usage

### Local Execution

Run the main script directly:
```sh
python gdocs_4_ski_automation/service.py
```

### Cloud Deployment

This service is designed to run as a Google Cloud Function. Deploy to Google Cloud Run and trigger via AppScript HTTP requests.

**Deployment URL**: [Google Cloud Run Console](https://console.cloud.google.com/)

## Project Structure

```
gdocs_4_ski_automation/
├── core/
│   ├── factories.py         # Registration factory for building objects from sheets
│   ├── mail_services.py     # Email sending and processing logic
│   ├── sheet_dumper.py      # Writing processed data back to sheets
│   ├── price_calculation.py # Pricing logic for registrations
│   └── ctypes.py           # Custom types and data structures
├── utils/
│   └── utils.py            # Google API authentication utilities
└── service.py              # Main entry point and orchestration

data/
├── dependencies/           # Credentials and configuration files
└── mails/                 # Email templates and attachments
```

## Dependencies

- `gspread`: Google Sheets API integration
- `pandas`: Data processing
- `openpyxl`: Excel file handling
- `jinja2`: Email template rendering
- `pyyaml`: Configuration file parsing
- `yagmail`: Email sending

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License.

## Author

Felix Schelling - [felix.schelling@protonmail.com](mailto:felix.schelling@protonmail.com)