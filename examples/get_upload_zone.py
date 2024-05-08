"""
Get upload zone example

"""
import os
import sys
import logging
import dotenv
from smartschoolapi_tkbstudios import SmartSchoolClient

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python examples/get_upload_zone.py <course_id>")
        sys.exit(1)

    course_id = int(sys.argv[1])

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

    upload_zone_dir = smart_school_client.get_upload_zone_dir(course_id=course_id, dir_id="0")[0]

    print("Upload zone:")
    print(f"ID: {upload_zone_dir['attributes']['id']}")
    print(f"Title: {upload_zone_dir['data']['title']}")
    print(f"State: {upload_zone_dir['state']}")
    if upload_zone_dir['data']['icon'] != "":
        print(f"Icon: {upload_zone_dir['data']['icon']}")
    print(f"Has children: {'yes ' if upload_zone_dir['hasChildren'] else 'no'}")

    for child in upload_zone_dir['children']:
        print("")
        child_data = smart_school_client.get_upload_zone_dir(
            course_id=course_id,
            dir_id=child['attributes']['id']
        )[0]

        print(f"ID: {child_data['attributes']['id']}")
        print(f"Title: {child_data['data']['title']}")
        print(f"State: {child_data['state']}")
        print(f"Icon: {child_data['data']['icon']}")
        print(f"Has children: {'yes ' if child_data['hasChildren'] else 'no'}")

    print("")
