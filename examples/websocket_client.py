"""
Websocket client example
"""
import os
import logging
import json
import dotenv
import smartschoolapi_tkbstudios as smsapi


def received_message_callback(message_data):
    """
    Callback function
    """
    print(message_data)
    message_text = message_data.get("text", None)
    if message_text == "pubsub message":
        message = message_data.get("message", None)
        if message is not None:
            message = json.loads(message)
            if message.get("type", None) == "notificationAlert":
                if message.get("module", None) == "Messages":
                    sender = message.get("title", None)
                    description = message.get("description", None)
                    url = message.get("url", None)
                    user_id = message.get("userID", None)
                    if sender is not None and description is not None and url is not None:
                        if user_id is not None:
                            print(f"Received message from {sender}: {description} - {url} - {user_id}")


if __name__ == '__main__':
    dotenv.load_dotenv()

    smart_school_client = smsapi.SmartSchoolClient(
        domain=os.getenv('SMARTSCHOOL_DOMAIN'),
        loglevel=logging.DEBUG,
    )
    smart_school_client.phpsessid = os.getenv('SMARTSCHOOL_PHPSESSID')
    smart_school_client.pid = os.getenv('SMARTSCHOOL_PID')
    smart_school_client.user_id = os.getenv('SMARTSCHOOL_USER_ID')
    smart_school_client.platform_id = os.getenv('SMARTSCHOOL_PLATFORM_ID')
    smart_school_client.received_message_callback = received_message_callback

    smart_school_client.check_if_authenticated()

    smart_school_client.run_websocket()
