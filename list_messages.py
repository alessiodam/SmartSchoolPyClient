import os
import logging
import time

import dotenv
from smartschoolclient import SmartSchoolClient


if __name__ == '__main__':
    os.makedirs("messages", exist_ok=True)
    dotenv.load_dotenv()

    smart_school_client = SmartSchoolClient(
        domain=os.getenv('SMARTSCHOOL_DOMAIN'),
        phpsessid=os.getenv('SMARTSCHOOL_PHPSESSID'),
        pid=os.getenv('SMARTSCHOOL_PID'),
        user_id=os.getenv('SMARTSCHOOL_USER_ID'),
        loglevel=logging.INFO,
    )

    messages = smart_school_client.list_messages()
    print("You have {} messages.".format(len(messages)))

    for message in messages:
        message_data = smart_school_client.get_message_by_id(message["id"])
        print("Message data:")
        print("Message ID: {}".format(message_data["id"]))
        print("From: {}".format(message_data["from"]))
        print("To: {}".format(message_data["to"] if message_data["to"] else "You"))
        print("CC: {}".format(message_data["ccreceivers"]))
        print("BCC: {}".format(message_data["bccreceivers"]))
        print("Subject: {}".format(message_data["subject"]))
        print("Date: {}".format(message_data["date"]))
        print("Status: {}".format("Read" if message_data["status"] == "1" else "Unread"))
        print("Attachment: {}".format(message_data["attachment"]))
        print("Body: {}".format(message_data["body"]))

        with open("messages/{}.txt".format(message_data["id"]), "w", encoding="utf-8") as f:
            f.write("Message data:\n")
            f.write("Message ID: {}\n".format(message_data["id"]))
            f.write("From: {}\n".format(message_data["from"]))
            f.write("To: {}\n".format(message_data["to"] if message_data["to"] else "You"))
            f.write("CC: {}\n".format(message_data["ccreceivers"]))
            f.write("BCC: {}\n".format(message_data["bccreceivers"]))
            f.write("Subject: {}\n".format(message_data["subject"]))
            f.write("Date: {}\n".format(message_data["date"]))
            f.write("Status: {}\n".format("Read" if message_data["status"] == "1" else "Unread"))
            f.write("Attachment: {}\n".format(message_data["attachment"]))
            f.write("Body: {}\n".format(message_data["body"]))

        time.sleep(1)
