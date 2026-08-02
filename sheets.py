import os
import requests

GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL")


def save_to_google_sheet(student_data):

    if not GOOGLE_SCRIPT_URL:
        print("GOOGLE_SCRIPT_URL is not set.")
        return False

    try:

        response = requests.post(
            GOOGLE_SCRIPT_URL,
            json=student_data,
            timeout=30,
        )

        print("Google Sheets Response:", response.text)

        return response.status_code == 200

    except Exception as e:
        print("Google Sheets Error:", str(e))
        return False