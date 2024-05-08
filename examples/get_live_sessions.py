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

    live_sessions = smart_school_client.get_live_sessions()

    online_session_meetings = live_sessions.get('online_session_meetings', [])
    parent_contacts = live_sessions.get('parent_contacts', [])

    if not online_session_meetings and not parent_contacts:
        print("No live sessions found.")
        exit()

    print("Live Sessions:")
    print("Online Session Meetings:")
    for online_session_meeting in online_session_meetings:
        print(online_session_meeting)
        print("\n")

    print("\n\n")
    print("Parent Contacts:")
    for parent_contact in parent_contacts:
        print(parent_contact)
