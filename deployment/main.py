"""Google Cloud Function entry point for ski course registration automation."""
import functions_framework
import logging
from typing import Dict, Any

from gdocs_4_ski_automation.service import run as run_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Configuration - these files must be uploaded to the cloud function
SHEET_IDS: Dict[str, str] = {
    "settings": "add id here",
    "registrations": "add registrationsid here",
    "db": "add db id here",
}

FILE_PATHS: Dict[str, str] = {
    "secrets_path": "client_secret.json",
    "mail_settings_path": "mail_setting.yaml",
    "paid_template_path": "paid.html",
    "registration_template_path": "registration.html",
    "checklist_path": "checklist.pdf",
    "mail_secret_path": "client_secret_mail.json",
}


@functions_framework.http
def main(request) -> tuple[str, int]:
    """HTTP Cloud Function entry point.
    
    Args:
        request: Flask request object.
        
    Returns:
        Tuple of (response_text, status_code).
    """
    logger.info("Cloud function triggered")
    
    # Optional: Verify authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        logger.warning("Missing or invalid authorization header")
        return "Unauthorized", 401
    
    try:
        # Run the service
        result = run_service(
            secrets_path=FILE_PATHS["secrets_path"],
            mail_settings_path=FILE_PATHS["mail_settings_path"],
            paid_template_path=FILE_PATHS["paid_template_path"],
            registration_template_path=FILE_PATHS["registration_template_path"],
            checklist_path=FILE_PATHS["checklist_path"],
            mail_secret_path=FILE_PATHS["mail_secret_path"],
            sheet_ids=SHEET_IDS,
        )
        
        logger.info("Service completed successfully")
        return f"Success: {result}", 200
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return f"Configuration error: {e}", 500
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return f"Error: {str(e)}", 500


if __name__ == "__main__":
    # For local testing
    class MockRequest:
        headers = {"Authorization": "Bearer test"}
    
    result, status = main(MockRequest())
    print(f"Status: {status}, Result: {result}")
