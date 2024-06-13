import random
import smtplib
from flask import Flask, jsonify, render_template, request, redirect, url_for
import mysql.connector
import uuid

app = Flask(__name__, template_folder=r'C:\Users\saina\Downloads\SoftwareEngineerProject\Bloodbank\hospital')

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'sai@38293829',
    'database': 'database2',
    'auth_plugin': 'mysql_native_password'
}
def connect_to_database():
    return mysql.connector.connect(**db_config)

@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ''  # Initialize error message
    if request.method == 'POST':
        # Retrieve form data
        email = request.form['email']
        password = request.form['password']

        # Check if user exists in the database
        if user_exists(email, password):
            print("success")
            return redirect(url_for('dashboard'))
        else:
            msg = 'Invalid credentials. Please try again.'
    return render_template('hospital_login.html', error_message=msg)


hospital_id=None


def user_exists(email, password):
    global hospital_id
    connection = connect_to_database()
    cursor = connection.cursor()
    print(connection.is_connected)
    # Prepare SQL query to check if user exists
    sql = "SELECT hospital_id FROM hospital_login WHERE email = %s AND password = %s"
    values = (email, password)

    # Execute the SQL query
    cursor.execute(sql, values)

    # Fetch one row
    user = cursor.fetchone()

    # Check if user exists
    if user:
        hospital_id = user[0] 
        print(hospital_id)# Only access user[0] if user is not None
        return True
    else:
        return False


@app.route('/dashboard')
def dashboard():
    return render_template('hospital_dashboard.html')


def get_admin_id(district_name):
    try:
        # Connect to MySQL database
        connection = connect_to_database()

        # Create cursor
        cursor = connection.cursor()
        # SQL query to fetch Admin_id based on district name
        sql_query = "SELECT Admin_id FROM dist_code WHERE dist1 = %s OR dist2 = %s OR dist3 = %s OR dist4 = %s"

        # Execute SQL query
        cursor.execute(sql_query, (district_name, district_name, district_name, district_name))

        # Fetch all records
        admin_ids = cursor.fetchone()

        # Close cursor and connection
        cursor.close()
        connection.close()
        if admin_ids:
            return admin_ids[0]
        else:
            return None
    
    except mysql.connector.Error as error:
        return jsonify({'error': str(error)}), 500



district_to_code = {
    "Srikakulam": "SRI01",
    "Parvathipuram Manyam": "PM02",
    "Vizianagaram": "VZ03",
    "Visakhapatnam": "VS04",
    "Alluri Sitharama Raju": "AS05",
    "Anakapalli": "AK06",
    "Kakinada": "KK07",
    "East Godavari": "EG08",
    "Dr. B. R. Ambedkar Konaseema": "KN09",
    "Eluru": "EL10",
    "West Godavari": "WG11",
    "NTR": "NT12",
    "Krishna": "KR13",
    "Palnadu": "PL14",
    "Guntur": "GU15",
    "Bapatla": "BP16",
    "Prakasam": "PR17",
    "Sri Potti Sriramulu Nellore": "NE18",
    "Kurnool": "KU19",
    "Nandyal": "NN20",
    "Anantapur": "AN21",
    "Sri Sathya Sai": "SS22",
    "YSR": "CU23",
    "Annamayya": "AM24",
    "Tirupati": "TR25",
    "Chittoor": "CH26"
}

@app.route('/submit_request', methods=['GET', 'POST'])
def form():
    connection = connect_to_database()
    cursor = connection.cursor()
    if request.method == 'POST':
        # Get form data
        name = request.form['fname']
        age = request.form['Age']
        district = request.form['District']
        address = request.form['Address']
        gender = request.form['Gender']
        blood_group = request.form['Blood_Group']
        reason = request.form['Reason']
        hospitalname = request.form['hospitalname']
        quantity = request.form['Quantity']
        optional_details = request.form['Optional']
        deadline = request.form['Deadline']
        
        # Convert district name to code
        district_code = district_to_code[district]
        
        # Generate unique form ID
        form_id = str(uuid.uuid4().hex)[:8]
        
        # Check if the generated form ID already exists in the database
        while form_id_exists(form_id):
            form_id = str(uuid.uuid4().hex)[:8]
        
        # Get the Admin_id for the district
        admin_id = get_admin_id(district_code)
        
        if admin_id is not None:
            # Insert form data into the database
            sql = """INSERT INTO forms (Admin_id, hospital_id, form_id, hospitalname, name, age, district, address, gender, blood_group, reason, quantity, optional_details, deadline) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            val = (admin_id, hospital_id, form_id, hospitalname, name, age, district, address, gender, blood_group, reason, quantity, optional_details, deadline)
            cursor.execute(sql, val)
            connection.commit()
            
            # Redirect to a success page or dashboard
            return redirect(url_for('dashboard'))
        else:
            # Handle the case when Admin_id is not found
            error_message = "Admin_id not found for the district. Please contact support."
            return render_template('request.html', error_message=error_message)

    return render_template('request.html')


def form_id_exists(form_id):
    connection = connect_to_database()
    cursor = connection.cursor()    
    cursor.execute("SELECT COUNT(*) FROM forms WHERE form_id = %s", (form_id,))
    count = cursor.fetchone()[0]
    return count > 0

@app.route('/history')
def blood_donation_history():
    # Connect to the SQLite database
    connection = connect_to_database()
    cursor = connection.cursor()
    
    # Fetch donation history from the database
    cursor.execute("SELECT name, age, address, gender, blood_group, reason, quantity, status FROM forms WHERE hospital_id = %s", (hospital_id,))
    donation_history = cursor.fetchall()
    print(donation_history)
    # Close the database connection
    connection.close()

    # Pass donation_history to the template
    return render_template('history.html', donation_history=donation_history)



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
@app.route('/verify_email')
def email_verification():
    return render_template('verify_email.html')

otp1=None
email1=None
# Route for verifying OTP
@app.route('/verify_otp', methods=['POST'])
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


@app.route('/verify_otp_page', methods=['GET', 'POST'])
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
@app.route('/resend_otp', methods=['POST'])
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
@app.route('/create_password', methods=['GET', 'POST'])
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
            update_query_donations = "UPDATE hospital_login SET password = %s WHERE email = %s"
            update_values_donations = (confirm_password,email1)
            print(confirm_password,email1)
            cursor.execute(update_query_donations, update_values_donations)
            return redirect(url_for('password_updated')) 
    else:
        return render_template('new_password.html')

# Route for rendering the password updated page
@app.route('/password-updated')
def password_updated():
    return redirect('/')


@app.route('/logout.html')
def logout():
    return render_template(('logout.html'))

if __name__ == '__main__':
    app.run(debug=True)