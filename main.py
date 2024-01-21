import sqlite3
from functions import *
import hashlib


# Cybersecurity
SALT = '^+@r4FGb{?Xi'

# Global variables
connection = sqlite3.connect('nusdates.db')
cursor = connection.cursor()
current_user_id = 0


# SQL Database Functions
def get_user_id(username, update=False):
    """
    Gets user_id from the SQLite database, updates the current_user_id if required
    :param username:
    :param update:
    :return:
    """
    result = cursor.execute("SELECT user_id from users WHERE username = @username", (username,))
    user_id = result.fetchone()[0]
    if update:
        global current_user_id
        current_user_id = user_id
    return user_id


def add_user(username, password):
    """
    Add a new user to the SQLite database
    :param username:
    :param password:
    :return: None
    """
    database_password = f'{password}{SALT}'
    hashed_password = hashlib.sha512(database_password.encode())
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password.hexdigest()))
    connection.commit()


def add_timetable(url):
    """
    Adds a user's timetable to the SQLite database
    :param url: NUSMods Timetable sharing link
    :return: None
    """
    timetable_data = []  # Format: [(course, lesson_type, class_number, day, start_time, end_time), etc.]
    courses_to_timeslots = parse_timetable_link(url)
    for course in courses_to_timeslots:
        if not courses_to_timeslots[course]:
            timetable_data.append((course, '', '', '', '', ''))
        for lesson_type, class_number in courses_to_timeslots[course]:
            day, start_time, end_time = get_timeslot_day_time(course, lesson_type, class_number)
            timetable_data.append((course, lesson_type, class_number, day, start_time, end_time))
    cursor.executemany("INSERT INTO timetables (course, lesson_type, class_number, day, start_time, end_time) "
                       "VALUES(?, ?, ?, ?, ?, ?)", timetable_data)
    cursor.execute('UPDATE timetables SET user_id = @user_id WHERE user_id IS NULL', (current_user_id,))
    connection.commit()


def match_timetables(friend_username):
    """
    Match current user's timetable with friend's timetable
    :param friend_username:
    :return: matching_timeslots, [(course, lesson_type): {class_number: venue, etc.}, etc.]
    """
    matching_timeslots = {}
    friend_user_id = get_user_id(friend_username)
    result = cursor.execute(
        "SELECT course, lesson_type, day, start_time, end_time FROM timetables "
        "WHERE user_id = @current_user_id or user_id = @friend_user_id "
        "GROUP BY course, lesson_type, day, start_time, end_time "
        "HAVING COUNT(*) = 2;",
        (current_user_id, friend_user_id)
    )
    matching_lessons = result.fetchall()
    for lesson in matching_lessons:
        course, lesson_type, day, start_time, end_time = lesson
        matching_timeslots[(course, lesson_type)] = get_matching_timeslots(
            course, lesson_type, day, start_time, end_time
        )
    return matching_timeslots


if __name__ == '__main__':
    pass
