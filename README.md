# gdocs_4_ski_automation
Automation scripts for Google Docs to automate ski course registration (g.Forms) related tasks


# What is this project?

This project contains automation scripts for Google Docs to streamline ski course registration tasks using Google Forms.

# Features

- Automates the creation and management of Google Forms for ski course registration.
- Integrates with Google Sheets to track and manage registrations.
- Sends automated email notifications to participants.

# Requirements

- OAuth 2.0 credentials for Google API access

# Installation

1. Clone the repository:
    ```sh
    git clone /home/felix/Documents/gdocs_automation/gdocs_4_ski_automation
    ```
2. Navigate to the project directory:
    ```sh
    cd gdocs_4_ski_automation
    ```
3. Install the required dependencies:
    ```sh
    pip install -e .
    ```

# Usage

1. Set up your Google API credentials.
2. get api desktop credentails and service credential and past them somewere
3. generate email templates and change mail service functions to provide correct data to html temple
4. adapt paths in service.py
5. Run the main script:
    ```sh
    python ./gdocs_4_ski_automation/service.py   
    ```
this lib is intended to run as cloud function, witch gets triggert throw a simple AppScript HttpRequest

# Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

# License

This project is licensed under the MIT License.