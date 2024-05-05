"""
Websocket client example
"""
import os
import logging
import dotenv
from smartschoolclient import SmartSchoolClient


def received_message_callback(sender, description, url, user_id):
    """
    Callback function
    """
    print(f"Received notification from {sender}: {description} ({url}) (User ID: {user_id})")


if __name__ == '__main__':
    dotenv.load_dotenv()

    smart_school_client = SmartSchoolClient(
        domain=os.getenv('SMARTSCHOOL_DOMAIN'),
        phpsessid=os.getenv('SMARTSCHOOL_PHPSESSID'),
        pid=os.getenv('SMARTSCHOOL_PID'),
        user_id=os.getenv('SMARTSCHOOL_USER_ID'),
        loglevel=logging.INFO,
        received_message_callback=received_message_callback
    )

    smart_school_client.run_websocket()
