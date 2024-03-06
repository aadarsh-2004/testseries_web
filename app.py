from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

import mysql.connector

app = Flask(__name__, template_folder='templates')
app.secret_key = 'sk'  # Replace 'your_secret_key' with a secure secret key

# Configure your MySQL database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="testseries"
)

cursor = db.cursor()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Query the database for the user
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    cursor.execute(query, (username, password))
    result = cursor.fetchall()

    # Check if the user exists
    if result:
        # Set the 'username' key in the session
        session['username'] = username
        return redirect(url_for('dashboard'))
    else:
        return 'Invalid username or password'

@app.route('/dashboard')
def dashboard():
    # Check if the user is logged in
    if 'username' in session:
        return render_template('dashboard.html')
    else:
        # If the user is not logged in, redirect to the login page
        return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Retrieve signup form data
        username = request.form['username']
        password = request.form['password']

        # Check if the username is already taken
        check_username_query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(check_username_query, (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Username already taken. Choose a different username.', 'error')
            return redirect(url_for('signup'))

        # Perform signup logic and database operations
        insert_user_query = "INSERT INTO users (username, password, subscription) VALUES (%s, %s, %s)"
        cursor.execute(insert_user_query, (username, password, "True"))

        # Commit changes to the database
        db.commit()

        flash('Signup successful. Please log in.', 'success')
        return redirect(url_for('index'))

    # Render the signup page for GET requests
    return render_template('signup.html')

@app.route('/testpaper')
def testpaper():
    # Check if the user is logged in
    if 'username' in session:
        # Query the database for the subscription status
        subscription_query = "SELECT subscription FROM users WHERE username = %s"
        cursor.execute(subscription_query, (session['username'],))
        subscription_status = cursor.fetchone()[0]

        # Check if the subscription status is 'True' (case insensitive)
        if subscription_status.lower() == 'true':
            # Get the page number from the request parameters (default to 1 if not provided)
            page_number = int(request.args.get('page', 1))

            # Calculate the offset based on the page number
            offset = (page_number - 1) * 10  # Assuming 10 questions per page

            # Fetch total number of questions from the database
            cursor.execute("SELECT COUNT(*) FROM questions")
            total_questions = cursor.fetchone()[0]

            # Calculate the total number of pages
            total_pages = (total_questions + 9) // 10  # Assuming 10 questions per page

            # Fetch questions from the database for the specified page
            cursor.execute(f"SELECT * FROM questions LIMIT 10 OFFSET {offset}")
            questions = cursor.fetchall()

            return render_template('testpaper.html', questions=questions, page_number=page_number, total_pages=total_pages)
            
        else:
            flash('You are not subscribed. Please subscribe to access the test paper.', 'error')
            return render_template('subscribe.html')
    else:
        # If the user is not logged in, redirect to the login page
        return redirect(url_for('index'))



# Route to display the questions
@app.route('/questions')
def display_questions():
    # Get the page number from the request parameters (default to 1 if not provided)
    page_number = int(request.args.get('page', 1))

    # Calculate the offset based on the page number
    offset = (page_number - 1) * 10  # Assuming 10 questions per page


    # Fetch questions from the database for the specified page
    cursor.execute(f"SELECT * FROM questions LIMIT 10 OFFSET {offset}")
    questions = cursor.fetchall()

    # Render the HTML template with the fetched questions
    return render_template('testpaper.html', questions=questions, page_number=page_number)

@app.route('/submit', methods=['POST'])
def submit_test():
    if 'username' in session:
        # Fetch correct answers from the database (fetch only once)
        cursor.execute("SELECT question_id, correct_answer FROM questions")
        correct_answers_data = cursor.fetchall()
        correct_answers = {str(question_id): correct_answer.upper() for question_id, correct_answer in correct_answers_data}

        # Get the user's submitted answers from the form data
        submitted_answers = {}
        for key, value in request.form.items():
            if key.startswith('q'):
                question_id = key[1:]
                user_answer = value.lower()
                submitted_answers[question_id] = user_answer

        # Print form data for debugging
        print("Form Data:", request.form)

        # Print submitted answers for debugging
        print("Submitted Answers:", submitted_answers)

        # Calculate the result
        total_questions = len(correct_answers)
        total_score = 0
        correct_answers_count = 0
        unattempted_count = 0

        for question_id, correct_answer in correct_answers.items():
            user_answer = submitted_answers.get(question_id, '')

            # Convert user answer to uppercase
            user_answer = user_answer.upper()

            # Debugging: print submitted answers
            print(f"Question {question_id}: User - {user_answer}, Correct - {correct_answer}")

            if user_answer == '':
                unattempted_count += 1
            elif user_answer == correct_answer:
                correct_answers_count += 1
                total_score += 1

        result_details = {
            'total_score': total_score,
            'correct_answers_count': correct_answers_count,
            'unattempted_count': unattempted_count
        }

        # For AJAX response, return JSON instead of rendering the template
        return jsonify(result_details)
    else:
        # If the user is not logged in, redirect to the login page
        flash('Please log in to submit the test.', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=2000)
