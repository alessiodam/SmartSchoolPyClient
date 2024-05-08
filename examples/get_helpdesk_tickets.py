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

    helpdesk_filters_json = smart_school_client.get_helpdesk_tickets_filters()
    helpdesk_filter_ids = [
        filter_json['id'] for filter_json in helpdesk_filters_json
    ]

    for filter_id in helpdesk_filter_ids:
        tickets = smart_school_client.get_helpdesk_tickets_by_filter_id(filter_id)
        if tickets is None:
            print(f'No filter found with ID {filter_id}')
            continue
        if tickets['tickets'] is None or len(tickets['tickets']) == 0:
            print(f'No tickets found for filter {filter_id}')
            continue
        for ticket in tickets['tickets']:
            print(ticket)
