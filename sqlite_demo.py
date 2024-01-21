import sqlite3
con = sqlite3.connect("test.db")

# idk what a cursor is
cur = con.cursor()

# usage: data is an array in the format: userid, username, password, name
def add_user(user):
    cur.executemany("INSERT INTO user VALUES(?, ?, ?, ?)", user)
    con.commit()

def add_timetable(userid, timetable):
    cur.executemany("INSERT INTO timetable (course_code, lesson_type, class_number) VALUES(?, ?, ?)", timetable)
    cur.execute("UPDATE timetable SET userid = @userid WHERE userid IS NULL", (userid,))
    con.commit()

def add_timetable_time(start_time, end_time, day, course_code, lesson_type, class_number, userid):
    cur.execute("UPDATE timetable SET start_time = ? WHERE userid = ? AND lesson_type = ? AND class_number = ? AND course_code = ?", (start_time, userid, lesson_type, class_number, course_code))
    cur.execute("UPDATE timetable SET end_time = ? WHERE userid = ? AND lesson_type = ? AND class_number = ? AND course_code = ?", (end_time, userid, lesson_type, class_number, course_code))
    cur.execute("UPDATE timetable SET day = ? WHERE userid = ? AND lesson_type = ? AND class_number = ? AND course_code = ?", (day, userid, lesson_type, class_number, course_code))
    con.commit()

userid = 1
day = 'Tuesday'

# below is format for user data
user = [
    (1, "BEN", "secretpassword", "Ben")
]

# below is format for timetable data
timetable = [
    ("CS2040C", "LAB", "07"),
    ("CG2111A", "LAB", "03"),
    ("MA1508E", "TUT", "03"),
    ("CS1231", "TUT", "04"),
    # etc depending on number of mods
]

# add_user(data)
add_timetable(userid, timetable)
add_timetable_time(1400, 1600, day, *(timetable[0]), userid)
# add_timetable_time(1400, 1600, day, "CS2040C", "LAB:07", userid)