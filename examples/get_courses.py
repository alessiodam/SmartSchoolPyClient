"""
Websocket client example
"""
import os
import logging
import dotenv
import smartschoolapi_tkbstudios as smsapi


if __name__ == '__main__':
    dotenv.load_dotenv()

    smart_school_client = smsapi.SmartSchoolClient(
        domain=os.getenv('SMARTSCHOOL_DOMAIN'),
        loglevel=logging.DEBUG,
    )
    smart_school_client.phpsessid = os.getenv('SMARTSCHOOL_PHPSESSID')
    smart_school_client.pid = os.getenv('SMARTSCHOOL_PID')
    smart_school_client.user_id = os.getenv('SMARTSCHOOL_USER_ID')

    courses = smart_school_client.get_courses()

    print("Your courses:")
    for course in courses:
        print("{} - {} - {}".format(course['id'], course['name'], course['teacher']))
