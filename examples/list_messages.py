"""
List messages example
"""
import os
import logging
import time
import dotenv
from smartschoolapi_tkbstudios import SmartSchoolClient


if __name__ == '__main__':
    os.makedirs("messages", exist_ok=True)
    dotenv.load_dotenv()

    smart_school_client = SmartSchoolClient(
        domain=os.getenv('SMARTSCHOOL_DOMAIN'),
        loglevel=logging.DEBUG,
    )
    smart_school_client.phpsessid = os.getenv('SMARTSCHOOL_PHPSESSID')
    smart_school_client.pid = os.getenv('SMARTSCHOOL_PID')
    smart_school_client.user_id = os.getenv('SMARTSCHOOL_USER_ID')
    smart_school_client.platform_id = os.getenv('SMARTSCHOOL_PLATFORM_ID')

    smart_school_client.check_if_authenticated()

    messages = smart_school_client.list_messages()
    print(f"You have {len(messages)} messages.")

    for message in messages:
        message_data = smart_school_client.get_message_by_id(message["id"])
        print("Message data:")
        print(f"Message ID: {message_data['id']}")
        print(f"From: {message_data['from']}")
        print(f"To: {message_data['to'] if message_data['to'] else 'You'}")
        print(f"CC: {message_data['ccreceivers']}")
        print(f"BCC: {message_data['bccreceivers']}")
        print(f"Subject: {message_data['subject']}")
        print(f"Date: {message_data['date']}")
        print(f"Status: {'Read' if message_data['status'] == '1' else 'Unread'}")
        print(f"Attachment: {message_data['attachment']}")
        print(f"Body: {message_data['body']}")

        with open(f"messages/{message_data['id']}.txt", "w", encoding="utf-8") as f:
            f.write("Message data:\n")
            f.write(f"Message ID: {message_data['id']}\n")
            f.write(f"From: {message_data['from']}\n")
            f.write(f"To: {message_data['to'] if message_data['to'] else 'You'}\n")
            f.write(f"CC: {message_data['ccreceivers']}\n")
            f.write(f"BCC: {message_data['bccreceivers']}\n")
            f.write(f"Subject: {message_data['subject']}\n")
            f.write(f"Date: {message_data['date']}\n")
            f.write(f"Status: {'Read' if message_data['status'] == '1' else 'Unread'}\n")
            f.write(f"Attachment: {message_data['attachment']}\n")
            f.write(f"Body: {message_data['body']}\n")

        time.sleep(1)
