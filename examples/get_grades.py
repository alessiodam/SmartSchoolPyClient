"""
Get grades example
"""
import os
import logging
import dotenv
import smartschoolapi_tkbstudios as smsapi


def format_grade(grade_to_format):
    """
    Format grade
    """
    course_name = grade_to_format['courses'][0]['name']
    grade_name = grade_to_format['name']
    grade_percentage = grade_to_format['graphic']['value']
    grade_description = grade_to_format['graphic']['description']
    grade_date = grade_to_format['date']
    grade_available_since_date = grade_to_format['availabilityDate']
    teacher_name = grade_to_format['gradebookOwner']['name']['startingWithLastName']
    period_name = grade_to_format['period']['name']
    period_active = bool(grade_to_format['period']['isActive'])

    feedbacks = grade_to_format.get('feedbacks', [])
    feedback_str = ""
    for feedback in feedbacks:
        student_name = feedback['student']['name']['startingWithLastName']
        teacher_name = feedback['teacher']['name']['startingWithLastName']
        feedback_text = feedback['text']
        feedback_str += f"\nFeedback for {student_name} from {teacher_name}:\n  {feedback_text}\n"

    return f"Course: {course_name}\n" \
           f"Grade: {grade_name}\n" \
           f"Grade: {grade_percentage}{'%' if isinstance(grade_percentage, int) else ''}" \
           f" - {grade_description}\n" \
           f"Date: {grade_date}\n" \
           f"Available since: {grade_available_since_date}\n" \
           f"Teacher: {teacher_name}\n" \
           f"Period: {period_name}{' - Active period!' if period_active else ''}\n" \
           f"{f"Feedbacks: {feedback_str}" if feedback_str else ''}"


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

    grades = smart_school_client.get_results()

    for grade in reversed(grades):
        formatted_grade = format_grade(grade)
        print(formatted_grade)
        print("\n")
