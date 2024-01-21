"""Contains helper functions that are used in the main script"""

import json
import requests
import os

# API Constants
NUSMODS_API_URL = 'https://api.nusmods.com/v2'
ACAD_YEAR = '2023-2024'
SEM = 2
SEMESTER = 'semester'
MODULES = 'modules'
JSON_SUFFIX = '.json'
TIMETABLE = 'timetable'
SEMESTER_DATA = 'semesterData'
CLASS_NUMBER = 'classNo'
LESSON_TYPE = 'lessonType'
VENUE = 'venue'
DAY = 'day'
START_TIME = 'startTime'
END_TIME = 'endTime'


# input validation for url

def parse_timetable_link(url):
    """
    :param url: NUSMods Timetable sharing link
    :return: courses_to_timeslots, {course: [(lesson_type, class_number), (lesson_type, class_number)]}
    """
    courses_to_timeslots = {}
    truncated_url = url.split('?')[-1]
    courses_and_timeslots = truncated_url.split('&')
    for course_and_timeslot in courses_and_timeslots:
        course, timeslots = course_and_timeslot.split('=')
        if timeslots:
            courses_to_timeslots[course] = [tuple(timeslot.split(':')) for timeslot in timeslots.split(',')]
        else:
            courses_to_timeslots[course] = []

    return courses_to_timeslots


def get_classes_details(course):
    """
    :param course:
    :return: class_details, {'classNo': class_number, etc.}
    """
    http_response = requests.get(os.path.join(NUSMODS_API_URL, ACAD_YEAR, MODULES, f'{course}{JSON_SUFFIX}'))
    course_details = json.loads(http_response.content)
    for semester_data in course_details[SEMESTER_DATA]:
        if semester_data[SEMESTER] == SEM:
            return semester_data[TIMETABLE]


def get_timeslot_day_time(course, lesson_type, class_number):
    """
    :param course:
    :param lesson_type:
    :param class_number:
    :return: day, start_time, end_time
    """
    classes_details = get_classes_details(course)

    for class_details in classes_details:
        if class_details[LESSON_TYPE].upper().startswith(lesson_type) and class_details[CLASS_NUMBER] == class_number:
            return class_details[DAY], class_details[START_TIME], class_details[END_TIME]


def get_matching_timeslots(course, lesson_type, day, start_time, end_time):
    """
    :param course:
    :param lesson_type:
    :param day:
    :param start_time:
    :param end_time:
    :return: matching_timeslots_to_locations, {class_number: venue, etc.}
    """
    matching_timeslots_to_locations = {}
    classes_details = get_classes_details(course)
    for class_details in classes_details:
        if class_details[LESSON_TYPE].upper().startswith(lesson_type) and \
                class_details[DAY] == day and \
                class_details[START_TIME] == start_time and \
                class_details[END_TIME] == end_time:
            matching_timeslots_to_locations[class_details[CLASS_NUMBER]] = class_details[VENUE]

    return matching_timeslots_to_locations
