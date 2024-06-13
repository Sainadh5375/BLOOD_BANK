from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import random
import string
import mysql.connector
import smtplib
from datetime import timedelta


application = Flask(__name__,template_folder=r'C:\Users\saina\Downloads\SoftwareEngineerProject\Bloodbank\users')
application.secret_key = 'your_secret_key'

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'sai@38293829',
    'database': 'database2',
    'auth_plugin': 'mysql_native_password'
}

def connect_to_database():
    return mysql.connector.connect(**db_config)

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def generate_12_digit_code():
    return ''.join(random.choices(string.digits, k=12))

def code_exists(code, cursor):
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE registration_id = %s", (code,))
    count = cursor.fetchone()[0]
    return count > 0

def generate_new_code(cursor):
    code = generate_12_digit_code()
    while code_exists(code, cursor):
        code = generate_12_digit_code()
    return code

unique_code1=None
unique_code12=None
@application.route('/signup.html', methods=['GET', 'POST'])
def signup():
    global unique_code1,unique_code12
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute("SELECT user_id FROM users_prof WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            return redirect(url_for('login'))
        unique_code = generate_code()
        cursor.execute("SELECT * FROM users_prof WHERE user_id = %s", (unique_code,))
        while cursor.fetchone():
            unique_code = generate_code()
        cursor.execute("INSERT INTO users_prof (user_id, email, password) VALUES (%s, %s, %s)", (unique_code, email, password))
        unique_code1 = unique_code
        connection.commit()
        cursor.close()
        connection.close()  
        return redirect(url_for('create_profile'))
    return render_template('signup.html')


@application.route('/login.html', methods=['GET', 'POST'])
def login():
    error_message = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT user_id FROM users_prof WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        if user:
            session['user_id'] = user['user_id']
            return redirect(url_for('user_home'))  # Redirect to user_home route
        else:
            error_message = "Invalid email or password. Please try again."
    return render_template('login.html', error_message=error_message)


@application.route('/user_home',methods=['GET', 'POST'])
def user_home():
    return render_template('user_home.html')




@application.route('/user_profile')
def user_profile():
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT first_name, last_name, dob, phone, age, district, address, gender FROM users_profile WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    return render_template('profiledash.html', user=user)


@application.route('/update_profile', methods=['GET', 'POST'])
def update_user_profile():
    if request.method == 'POST':
        # Extract form data
        username = request.form['fname']
        email = request.form['email']
        address = request.form['address']
        phone = request.form['phone']
        district = request.form['district']
        country = request.form['country']

        # Connect to the database
        connection = connect_to_database()
        cursor = connection.cursor()

        # Update user profile in the database
        sql = "UPDATE users_profile SET first_name = %s, email = %s, address = %s, phone = %s, district = %s, country = %s WHERE id = %s"
        values = (username, email, address, phone, district, country, session['user_id'])
        cursor.execute(sql, values)
        connection.commit()
        sample_data=[]
        
        # Fetch updated user data
        cursor.execute("SELECT first_name, email, address, phone, district, country FROM users_profile WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        sample_data.append({
            'fname': user['first_name'],
            'email': user['email'],
            'address': user['address'],
            'phone': user['phone'],
            'district': user['district'],
            'gender':user['gender'],
            'hospital': user['hospitalname'],
            'address': user['address'],
            'disease': user['reason'],
            'deadline': user['deadline'],
            'details': user['optional_details'],
            'district': user['district'],
            'address_district': user['district']  # Not sure what you intend here
        })
        # Close cursor and connection
        cursor.close()
        connection.close()

        # Pass user data to the template
        return render_template('update_profile.html', user=user)
    else:
        # Handle GET request if needed (e.g., display a form for updating profile)
        # For simplicity, you can redirect to the profile update page
        return render_template('update_profile.html')



def insert_appointment(appointment_date, appointment_time, selected_district, cursor):
    try:
        global code_for_thankyou
        registration_id = generate_new_code(cursor)
        cursor.execute("INSERT INTO appointments (login_id, registration_id, appointment_date, appointment_time, district) VALUES (%s, %s, %s, %s, %s)",
                       (session['user_id'], registration_id, appointment_date, appointment_time, selected_district))
        code_for_thankyou = registration_id
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print("MySQL Error:", e.msg)
        return False
    except Exception as e:
        print("Error inserting appointment data:", e)
        return False


@application.route('/')
def index():
    return render_template('home.html') 



@application.route('/appointment.html', methods=['GET', 'POST'])
def appointment():
    if request.method == 'POST':
        appointment_date = request.form['appointment-date']
        appointment_time = request.form['appointment-time']
        selected_district = request.form['select-dist']
        session['appointment_details'] = {
            'appointment_date': appointment_date,
            'appointment_time': appointment_time,
            'selected_district': selected_district
        }
        return redirect(url_for('donate'))
    return render_template('appointment.html')



@application.route('/donate.html', methods=['POST', 'GET'])
def donate():
    if request.method == 'POST':
        appointment_details = session.pop('appointment_details', None)
        if not appointment_details:
            return "Appointment details not found. Please try again."
        try:
            fname = request.form['fname']
            lname = request.form['lname']
            dob = request.form['Dob']
            aadhar_no = request.form['Aadhar_no']
            email = request.form['Email']
            phone_no = request.form['phone_no']
            age = request.form['Age']
            district = request.form['District']
            address = request.form['Address']
            postal_code = request.form['PostalCode']
            occupation = request.form['Occupation']
            gender = request.form['Gender']
            blood_group = request.form['Blood_Group']
            blood_donated_before = request.form['before11']
            diseases = request.form.get('Disease', '')
            connection = connect_to_database()
            cursor = connection.cursor()
            print(session['user_id'])
            if insert_appointment(appointment_details['appointment_date'], 
                                  appointment_details['appointment_time'], 
                                  appointment_details['selected_district'], cursor):
                sql = "INSERT INTO donations (login_id, registration_id, first_name, last_name, dob, aadhar_no, email, phone_no, age, district, address, postal_code, occupation, gender, blood_group, blood_donated_before, diseases) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (session['user_id'], code_for_thankyou, fname, lname, dob, aadhar_no, email, phone_no, age, district, address, postal_code, occupation, gender, blood_group, blood_donated_before, diseases))
                connection.commit()
                cursor.close()
                connection.close()
                return "Your donation has been successfully registered!"
            else:
                return "Failed to insert appointment."
        except mysql.connector.Error as e:
            print("MySQL Error:", e.msg)
            return "An error occurred while submitting the form."
        except Exception as e:
            print("Error:", e)
            return "An unexpected error occurred."
    return render_template('donate.html')





@application.route('/logout.html')
def logout():
    return render_template('logout.html')




@application.route('/history.html')
def history():
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT a.registration_id, a.appointment_date, "
                       "CONCAT(d.first_name, ' ', d.last_name) AS full_name, "
                       "d.gender, d.blood_group, d.status "
                       "FROM appointments a "
                       "INNER JOIN donations d ON a.login_id = d.login_id "
                       "WHERE a.login_id = %s", (session.get('user_id'),))
        appointments = cursor.fetchall()
        print(session.get('user_id'))
        print(appointments)
        
        # Convert data into a list of dictionaries
        data = []
        for appointment in appointments:
            data.append({
                'appointment_id': appointment[0],
                'appointment_date': appointment[1],
                'name': appointment[2],
                'gender': appointment[3],
                'blood_group': appointment[4],
                'status': appointment[5]
            })

        conn.close()
        return render_template('history.html', data=data)  # Pass 'data' to the template
    except Exception as e:
        # Log the error or display a generic error message
        print("An error occurred:", e)
        return "An error occurred while retrieving data."


@application.route('/create_profile', methods=['GET', 'POST'])
def create_profile():
    if request.method == 'POST':
        try:
            
            # Connect to the database
            db = connect_to_database()
            cursor = db.cursor()

            # Extract form data
            fname = request.form['fname']
            lname = request.form['lname']
            dob = request.form['Dob']
            email = request.form['Email']
            phone = request.form['phone_no']
            age = request.form['Age']
            district = request.form['District']
            address = request.form['Address']
            gender = request.form['Gender']

            # Debugging: Print session contents

            # SQL query to insert form data into the database
            sql = "INSERT INTO users_profile (id, first_name, last_name, dob, email, phone, age, district, address, gender) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            val = (unique_code1, fname, lname, dob, email, phone, age, district, address, gender)

            # Execute the SQL query
            cursor.execute(sql, val)

            # Commit changes to the database
            db.commit()

            # Close database connection
            cursor.close()
            db.close()

            return redirect('user_home')
        except Exception as e:
            return "An error occurred: " + str(e)
    else:
        # Handle GET request (if needed)
        return render_template('profile_creation.html')

# Function to send OTP email
def send_otp_email(email, otp):
    subject = "Your OTP"
    body = f"Your OTP is: {otp}"
    msg = f"Subject: {subject}\n\n{body}"
    try:
        s = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        s.ehlo()
        email_id = "v8481373@gmail.com"
        password = "ndwv orww kvcl rdbo"
        s.login(email_id, password)
        s.sendmail(email_id, email, msg)
        print("OTP sent successfully.")
    except Exception as e:
        print("An error occurred while sending OTP:", str(e))
    finally:
        s.quit()

# Function to generate OTP
def generate_otp():
    # Generate a random 4-digit OTP
    otp = ''.join(random.choices('0123456789', k=4))
    return otp

# Route for rendering the email verification page
@application.route('/verify_email')
def email_verification():
    return render_template('verify_email.html')

otp1=None
email1=None
# Route for verifying OTP
@application.route('/verify_otp', methods=['POST'])
def verify_otp():
    global otp1,email1
    if request.method == 'POST':
        email = request.form.get('email')  # Get the email from the form
        if email:
            email1=email
            print("Email entered:", email)  # Print the email for debugging
            otp1 = generate_otp()
            print(otp1)# Generate OTP
            send_otp_email(email, otp1)  # Send OTP via email
            # Redirect to verify_otp_page with the email and OTP
            return redirect(url_for('verify_otp_page', email=email, otp=otp1))
        else:
            return "No email entered."
    else:
        return "Invalid request method."

# Route for rendering the OTP verification page


@application.route('/verify_otp_page', methods=['GET', 'POST'])
def verify_otp_page():
    print(1)
    global otp1
    if request.method == 'POST':
        print(2)
        email = request.form.get('email')
        user_entered_otp = request.form.get('otp')
        print(otp1)
        print(user_entered_otp)
        if user_entered_otp == otp1:
            print("sucess")
            return redirect(url_for('create_password'))
        else:
            error = "Invalid OTP. Please try again."
            return render_template('verify_otp.html', email=email, otp=otp1, error=error)
    else:
        email = request.args.get('email')
        otp = request.args.get('otp')
        return render_template('verify_otp.html', email=email, otp=otp)
    

# Route for resending OTP
@application.route('/resend_otp', methods=['GET', 'POST'])
def resend_otp():
    if request.method == 'POST':
        email = request.form.get('email')  # Get the email from the form
        if email:
            print("Resending OTP to:", email)  # Print the email for debugging
            otp = generate_otp()  # Generate OTP
            send_otp_email(email, otp)  # Send OTP via email
            # Redirect to verify_otp_page with the email and OTP
            return redirect(url_for('verify_otp_page', email=email, otp=otp))
        else:
            return "No email entered."
    else:
        return "Invalid request method."

# Route for rendering the page to create a new password
@application.route('/create_password', methods=['GET', 'POST'])
def create_password():
    if request.method == 'POST':
        new_password = request.form.get('new-password')
        confirm_password = request.form.get('confirm-password')
        print(new_password,confirm_password)
        if new_password != confirm_password:
            error = "Passwords do not match"
            return render_template('new_password.html', error=error)
        else:
            connection = connect_to_database()
            cursor = connection.cursor(dictionary=True)
            update_query_donations = "UPDATE users SET password = %s WHERE email = %s"
            update_values_donations = (confirm_password,email1)
            print(confirm_password,email1)
            cursor.execute(update_query_donations, update_values_donations)
            return redirect(url_for('password_updated')) 
    else:
        return render_template('new_password.html')

# Route for rendering the password updated page
@application.route('/password-updated')
def password_updated():
    return redirect('/')

if __name__ == '__main__':
    application.run(debug=True)