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
        cursor.execute(insert_user_query, (username, password, "False"))

        # Commit changes to the database
        db.commit()

        flash('Signup successful. Please log in.', 'success')
        return redirect(url_for('index'))

    # Render the signup page for GET requests
    return render_template('signup.html')


@app.route('/testpaper', methods=['GET', 'POST'])
def testpaper():
    # Check if the user is logged in
    if 'username' in session:
        # Query the database for the subscription status
        subscription_query = "SELECT subscription FROM users WHERE username = %s"
        cursor.execute(subscription_query, (session['username'],))
        subscription_status = cursor.fetchone()[0]

        # Check if the subscription status is 'True' (case insensitive)
        if subscription_status.lower() == 'true':
            # Fetch all questions from the database
            cursor.execute("SELECT * FROM questions")
            questions = cursor.fetchall()

            # Render the HTML template with all questions
            return render_template('testpaper.html', questions=questions)
            
        else:
            flash('You are not subscribed. Please subscribe to access the test paper.', 'error')
            return render_template('subscribe.html')
    else:
        # If the user is not logged in, redirect to the login page
        return redirect(url_for('index'))


# Route to display all questions on one page
@app.route('/questions')
def display_all_questions():
    # Fetch all questions from the database
    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()

    # Render the HTML template with all questions
    return render_template('testpaper.html', questions=questions)

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
                user_answer = value.upper()  # Convert to uppercase for consistency
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

        

        # Render the result template and pass the result details
        return render_template('result.html', result_details=result_details)

    else:
        # If the user is not logged in, redirect to the login page
        flash('Please log in to submit the test.', 'error')
        return redirect(url_for('index'))

@app.route('/result')
def display_result():

    # You can add more logic here if needed
    return render_template('result.html')
@app.route('/subscribe', methods=['POST'])
def subscribe():
    if 'username' in session:
        # Retrieve subscription form data
        payment_method = request.form['payment_method']
        amount = request.form['amount']

        # Fetch any unread results from the previous query
        cursor.fetchall()

        # Update the user's subscription status in the database
        update_subscription_query = "UPDATE users SET subscription = %s WHERE username = %s"
        cursor.execute(update_subscription_query, ("True", session['username']))

        # Commit changes to the database
        db.commit()

        flash('Subscription successful. You can now access the test paper.', 'success')
        return redirect(url_for('dashboard'))
    else:
        # If the user is not logged in, redirect to the login page
        flash('Please log in to subscribe.', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=2000)
