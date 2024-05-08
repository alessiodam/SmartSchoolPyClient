"""
Get planner example

"""
import os
import logging
import dotenv
import smartschoolapi_tkbstudios as smsapi


def format_agenda_item(item_to_format):
    """
    Format agenda item
    """
    if 'courses' in item_to_format:
        if len(item_to_format['courses']) > 0:
            course = item_to_format['courses'][0]['name']
        else:
            course = 'No course'
    else:
        course = 'No course'
    return {
        'id': item_to_format['id'],
        'name': item_to_format['name'] if 'name' in item_to_format else 'No name',
        'course': course,
        'from_date': item_to_format['period']['dateTimeFrom'],
        'to_date': item_to_format['period']['dateTimeTo'],
        'whole_day': bool(item_to_format['period']['wholeDay']),
        'deadline': bool(item_to_format['period']['deadline']),
        'pinned': bool(item_to_format['pinned'])
    }


def print_item(item_to_print):
    """
    Print item
    """
    print(
        f"{item_to_print['name'] if item_to_print['name'] else ''} "
        f"in {item_to_print['course']} "
        f"from {item_to_print['from_date']} "
        f"to {item_to_print['to_date']}"
    )
    if item_to_print['whole_day']:
        print("Whole day")
    if item_to_print['deadline']:
        print("Deadline")
    if item_to_print['pinned']:
        print("Pinned")
    print()


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

    smart_school_client.check_if_authenticated()

    FROM_DATE = None
    TO_DATE = None
    planner_items = smart_school_client.get_planner(FROM_DATE, TO_DATE)

    for item in planner_items:
        print_item(format_agenda_item(item))
