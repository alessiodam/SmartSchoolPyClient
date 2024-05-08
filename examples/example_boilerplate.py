"""
Boilerplate
"""
import os
import logging
import dotenv
from smartschoolapi_tkbstudios import SmartSchoolClient


if __name__ == '__main__':
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

    # do things you want here
