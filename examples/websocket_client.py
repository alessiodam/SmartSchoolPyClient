"""
Websocket client example
"""
import os
import logging
import dotenv
import smartschoolapi_tkbstudios as smsapi


def received_message_callback(message_data):
    """
    Callback function
    """
    print(f"Received message: {message_data}")


if __name__ == '__main__':
    dotenv.load_dotenv()

    smart_school_client = smsapi.SmartSchoolClient(
        domain=os.getenv('SMARTSCHOOL_DOMAIN'),
        phpsessid=os.getenv('SMARTSCHOOL_PHPSESSID'),
        pid=os.getenv('SMARTSCHOOL_PID'),
        user_id=os.getenv('SMARTSCHOOL_USER_ID'),
        loglevel=logging.INFO,
        received_message_callback=received_message_callback
    )

    smart_school_client.run_websocket()
