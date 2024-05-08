"""
Boilerplate
"""
import os
import logging
import json
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

    intradesk_listing = smart_school_client.intradesk_get_directory()
    folders = intradesk_listing['folders']
    files = intradesk_listing['files']
    weblinks = intradesk_listing['weblinks']

    for folder in folders:
        print(folder['name'])
        print(f"  ID: {folder['id']}")
        print(f"  Date created: {folder['dateCreated']}")
        print(f"  Date changed: {folder['dateChanged']}")
        print(f"  Visible: {'yes' if folder['visible'] else 'no'}")
        print(f"  Confidential: {'yes' if folder['inConfidentialFolder'] else 'no'}")
        print(f"  Parent folder ID: {'yes' if folder['parentFolderId'] else 'no'}")
        print(f"  Favourite: {'yes' if folder['isFavourite'] else 'no'}")
        print(f"  Has children: {'yes' if folder['hasChildren'] else 'no'}")
        print("  Capabilities:")
        print(f"      Can manage: {'yes' if folder['capabilities']['canManage'] else 'no'}")
        print(f"      Can add: {'yes' if folder['capabilities']['canAdd'] else 'no'}")
        print(f"      Can see history: {'yes' if folder['capabilities']['canSeeHistory'] else 'no'}")
        print(f"      Can see view history: {'yes' if folder['capabilities']['canSeeViewHistory'] else 'no'}")

        print("\n")

    # TODO: files
    # TODO: weblinks
