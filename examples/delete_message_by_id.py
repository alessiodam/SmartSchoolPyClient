"""
Delete message example
How to use:
python `examples/delete_message_by_id.py 123`
where 123 is the message id

"""
import os
import logging
import sys
import dotenv
from smartschoolapi_tkbstudios import SmartSchoolClient

if __name__ == '__main__':
    dotenv.load_dotenv()

    if len(sys.argv) != 2:
        print("Usage: python examples/delete_message_by_id.py <message_id>")
        sys.exit(1)

    message_id = int(sys.argv[1])

    smart_school_client = SmartSchoolClient(
        domain=os.getenv('SMARTSCHOOL_DOMAIN'),
        loglevel=logging.DEBUG,
    )
    smart_school_client.phpsessid = os.getenv('SMARTSCHOOL_PHPSESSID')
    smart_school_client.pid = os.getenv('SMARTSCHOOL_PID')
    smart_school_client.user_id = os.getenv('SMARTSCHOOL_USER_ID')
    smart_school_client.platform_id = os.getenv('SMARTSCHOOL_PLATFORM_ID')

    smart_school_client.check_if_authenticated()

    messages = smart_school_client.delete_message_by_id(message_id)
