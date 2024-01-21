from flask import Flask, render_template, request, redirect, url_for, session, g
import requests
import sqlite3
from functions import *
import hashlib

# Cybersecurity
SALT = '^+@r4FGb{?Xi'

# Global variables
# connection = sqlite3.connect('nusdates.db')
# cursor = connection.cursor()
days_to_lessons = {'Sunday': {},
                   'Monday': {},
                   'Tuesday': {},
                   'Wednesday': {},
                   'Thursday': {},
                   'Friday': {},
                   'Saturday': {}}
current_user_id = 0


# SQL Database Functions
def get_user_id(username, update=False):
    """
    Gets user_id from the SQLite database, updates the current_user_id if required
    :param username:
    :param update:
    :return:
    """
    cursor = get_db()
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
    cursor = get_db()
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password.hexdigest()))
    cursor.commit()


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
    cursor = get_db()
    cursor.executemany("INSERT INTO timetables (course, lesson_type, class_number, day, start_time, end_time) "
                       "VALUES(?, ?, ?, ?, ?, ?)", timetable_data)
    cursor.execute('UPDATE timetables SET user_id = @user_id WHERE user_id IS NULL', (current_user_id,))
    cursor.commit()


def match_timetables(friend_username):
    """
    Match current user's timetable with friend's timetable
    :param friend_username:
    :return: matching_timeslots, [(course, lesson_type): {class_number: venue, etc.}, etc.]
    """
    matching_timeslots = {}
    friend_user_id = get_user_id(friend_username)
    db = get_db()
    cursor = db.execute(
        "SELECT course, lesson_type, day, start_time, end_time FROM timetables "
        "WHERE user_id = @current_user_id or user_id = @friend_user_id "
        "GROUP BY course, lesson_type, day, start_time, end_time "
        "HAVING COUNT(*) = 2;",
        (current_user_id, friend_user_id)
    )
    matching_lessons = [(row['course'], row['lesson_type'], row['day'], row['start_time'], row['end_time'])
                        for row in cursor.fetchall()]
    for lesson in matching_lessons:
        course, lesson_type, day, start_time, end_time = lesson
        matching_timeslots[(course, lesson_type, day, start_time, end_time)] = tuple(get_matching_timeslots(
            course, lesson_type, day, start_time, end_time
        ).items())[0]

    return matching_timeslots

    # # Sort data by day and time
    # global days_to_lessons
    # days_to_lessons = {'Sunday': {},
    #                    'Monday': {},
    #                    'Tuesday': {},
    #                    'Wednesday': {},
    #                    'Thursday': {},
    #                    'Friday': {},
    #                    'Saturday': {}}
    # for lesson in matching_timeslots:
    #     course, lesson_type, day, start_time, end_time = lesson
    #     days_to_lessons[day][(course, lesson_type, start_time, end_time)] = matching_timeslots[lesson]
    #
    # return days_to_lessons


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key
app.config['DATABASE'] = 'nusdates.db'  # SQLite database file

# OAuth configuration for Google
google_client_id = 'your_google_client_id'
google_client_secret = 'your_google_client_secret'
google_redirect_uri = 'your_redirect_uri'  # e.g., 'http://localhost:5000/google-login/callback'

google_authorization_base_url = 'https://accounts.google.com/o/oauth2/auth'
google_token_url = 'https://accounts.google.com/o/oauth2/token'
google_user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'


# Session timeout (set to 1 day for example)
# app.permanent_session_lifetime = timedelta(minutes=5)

# Function to connect to the database
def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


# Initialize the database
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


# Get the database connection
def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


def update_password(username, new_password):
    db = get_db()
    db.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, username))
    db.commit()


# Close the database connection when the app is closed
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def verify_user(username, password):
    db = get_db()
    cursor = db.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user and user['password'] == password:
        return True

    return False


def user_exists(username):
    db = get_db()
    cursor = db.execute('SELECT * FROM users WHERE username = ?', (username,))
    return cursor.fetchone() is not None


def add_user(username, password):
    db = get_db()
    db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    db.commit()


###function to connect database ends here###

###login and sign in pages start here###
@app.route("/")
def home():
    # Check if the user is logged in
    if 'username' in session:
        return render_template('home.html')
    else:
        return render_template('login.html')


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if the entered username exists and the password is correct
        if verify_user(username, password):
            session['username'] = username
            get_user_id(username, update=True)
            return redirect(url_for('home'))
        else:
            error = 'Invalid username or password. Please try again.'
            return render_template('login.html', error=error)

    return render_template('login.html')


@app.route("/logout", methods=['GET', 'POST'])
def logout():
    # Clear the session to log out the user
    session.pop('username', None)
    session.pop('google_token', None)
    return redirect(url_for('login'))


@app.route("/change_password", methods=['GET', 'POST'])
def change_password():
    if 'username' in session:
        if request.method == 'POST':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            # Verify the current password
            if verify_user(session['username'], current_password):
                # Check if the new password matches the confirmation
                if new_password == confirm_password:
                    # Update the password in the database
                    update_password(session['username'], new_password)
                    return redirect(url_for('home'))
                else:
                    error = 'New password and confirmation do not match.'
                    return render_template('change_password.html', error=error)
            else:
                error = 'Incorrect current password.'
                return render_template('change_password.html', error=error)

        return render_template('change_password.html')
    else:
        return redirect(url_for('login'))


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if the username is already taken
        if user_exists(username):
            error = 'Username is already taken. Please choose another.'
            return render_template('signup.html', error=error)

        # Add the new user to the database
        add_user(username, password)  # doesn't Hash the password

        # Redirect to the login page after sign-up
        return redirect(url_for('login'))

    return render_template('signup.html')


###sign up and log in pages end here###


@app.route("/save_timetable", methods=['POST'])
def save_timetable():
    if 'username' in session:
        timetable_link = request.form.get('timetableLink')
        # insert input validation
        add_timetable(timetable_link)
        return redirect(url_for('my_timetable'))


###google login code ###
@app.route("/google-login")
def google_login():
    google_params = {
        'client_id': google_client_id,
        'redirect_uri': google_redirect_uri,
        'scope': 'openid email',
        'response_type': 'code',
    }
    google_auth_url = f"{google_authorization_base_url}?{url_for('google_authorized')}"
    return redirect(google_auth_url)


@app.route('/google-login/callback')
def google_authorized():
    code = request.args.get('code')
    data = {
        'code': code,
        'client_id': google_client_id,
        'client_secret': google_client_secret,
        'redirect_uri': google_redirect_uri,
        'grant_type': 'authorization_code',
    }
    response = requests.post(google_token_url, data=data)

    if response.status_code == 200:
        token_data = response.json()
        session['google_token'] = (token_data['access_token'], '')
        user_info_response = requests.get(google_user_info_url,
                                          headers={'Authorization': 'Bearer ' + token_data['access_token']})
        user_info = user_info_response.json()

        # Now, you can use user_info to get user information (e.g., user_email = user_info['email'])

        # Perform your login logic here (e.g., create a session for the user)

        return redirect(url_for('home'))
    else:
        return 'Error during Google login'


### end of google log in code###

@app.route("/my_timetable")
def my_timetable():
    return render_template('my_timetable.html')


# Friends route
@app.route("/friends")
def friends():
    return render_template('friends.html')


@app.route("/find_friends", methods=["POST"])
def find_friends():
    search_input = request.form.get("search_input", "").lower()
    db = get_db()
    cursor = db.execute("SELECT username FROM users")
    usernames = [row['username'] for row in cursor.fetchall()]

    filtered_usernames = [username for username in usernames if username.lower().startswith(search_input)]

    return render_template("find_friends_results.html", filtered_usernames=filtered_usernames)


@app.route('/add_friend', methods=['POST'])
def add_friend():
    friend_username = request.form.get('friend_username')

    # Use the get_db function to get the database connection
    db = get_db()

    # Add the friend to the database (You might have a Friends table to store relationships)
    # This is a simplified example, and you should adjust it based on your database structure
    db.execute('INSERT INTO friends (user_id, friend_username) VALUES (?, ?)', (get_user_id(), friend_username))
    db.commit()

    # Redirect back to the Friends page
    return redirect(url_for('friends'))


# Match! route
@app.route("/match", methods=['GET', 'POST'])
def match():
    return render_template('match.html')


@app.route("/get_friend_username", methods=['GET', 'POST'])
def get_friend_username():
    if 'username' in session:
        friend_username = request.form.get('searchlink')
        same_timetable = request.form.get('same-timetable')  # Returns 'on' if checkbox is checked
        common_free_time = request.form.get('common-free-time')  # Returns 'on' if checkbox is checked

        db = get_db()
        cursor = db.execute("SELECT username FROM users WHERE username = @friend_username", (friend_username,))

        # If username exists
        if cursor.fetchone():
            global days_to_lessons
            matched_data = match_timetables(friend_username)

            print(days_to_lessons)

            # insert input validation
            return render_template(
                'match_result.html',
                data= matched_data)


# @app.route("/match_result", methods=['GET', 'POST'])
# def match_result():
#     print(matched_data)
#     return render_template('match_result.html', entries=matched_data)


# Groups route
@app.route("/groups")
def groups():
    return render_template('groups.html')


# My Account route
@app.route("/my_account")
def my_account():
    return render_template('my_account.html')


if __name__ == '__main__':
    # Check if the database exists; if not, initialize it
    # init_db()
    app.run(debug=True)
