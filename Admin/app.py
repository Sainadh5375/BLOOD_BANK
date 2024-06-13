import random
import smtplib
from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import mysql.connector
from datetime import datetime 

Admin_id=None

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'sai@38293829',
    'database': 'database2',
    'auth_plugin': 'mysql_native_password'
}




def connect_to_database():
    return mysql.connector.connect(**db_config)

app = Flask(__name__, template_folder=r'C:\Users\saina\Downloads\SoftwareEngineerProject\Bloodbank\BLOOD_PLANT')
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

@app.route('/', methods=['GET', 'POST'])
def index():
    global Admin_id
    error_message = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        print(email,password)
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT Admin_id FROM login WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        if user:
            session['user_id'] = user['Admin_id']
            Admin_id = user['Admin_id']
            print(Admin_id)
            return redirect('home')
        else:
            error_message = "Invalid email or password. Please try again."
            return render_template('admin_log.html', error_message=error_message)
    return render_template('admin_log.html', error_message=error_message)


    # Move this line outside of the if block to ensure it's always executed for GET requests

@app.route('/route')
def status():
    return render_template('route.html')

@app.route('/get_blood_bank_data', methods=['POST'])
def get_blood_bank_data():
    data = request.json
    set_name = data['setName']
    districts = data['districts']
    db_connection = connect_to_database()
    cursor = db_connection.cursor(dictionary=True)
    query = "SELECT * FROM BloodAvailability WHERE District IN (%s)" % ','.join(['%s'] * len(districts))
    cursor.execute(query, tuple(districts))
    results = cursor.fetchall()
    cursor.close()
    db_connection.close()
    blood_bank_data = {}
    for row in results:
        district = row['District']
        blood_bank_data[district] = {
            "A+": row["A_Positive"], "A-": row["A_Negative"], 
            "B+": row["B_Positive"], "B-": row["B_Negative"],
            "AB+": row["AB_Positive"], "AB-": row["AB_Negative"], 
            "O+": row["O_Positive"], "O-": row["O_Negative"]
        }
    return jsonify(blood_bank_data)

sample_data = []

def fetchdata():
    global Admin_id
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT form_id, name, age, blood_group, quantity,gender, hospitalname, address, reason, deadline, optional_details, district FROM forms WHERE admin_id = %s AND status = %s", (Admin_id, 'pending'))
    users = cursor.fetchall()
    
    sample_data = []  # Initialize sample_data list here
    for user in users:
        sample_data.append({
            'id': user['form_id'],
            'name': user['name'],
            'age': user['age'],
            'bloodType': user['blood_group'],
            'quantity': user['quantity'],
            'gender':user['gender'],
            'hospital': user['hospitalname'],
            'address': user['address'],
            'disease': user['reason'],
            'deadline': user['deadline'],
            'details': user['optional_details'],
            'district': user['district'],
            'address_district': user['district']  # Not sure what you intend here
        })
    print(sample_data)

    cursor.close()
    connection.close()
    return sample_data


@app.route('/submit_request', methods=['POST'])
def submit_request():
    global Admin_id

    # District codes mapping
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

    # Retrieve data from the form
    district = request.form.get('district')
    form_id = request.form.get('form_id')
    name = request.form.get('name')
    age = request.form.get('age')
    blood_type = request.form.get('bloodType')
    quantity = request.form.get('quantity')
    hospital = request.form.get('hospital')
    address = request.form.get('address')
    disease = request.form.get('disease')
    deadline = request.form.get('deadline')
    details = request.form.get('details')
    address_district = request.form.get('address_district')

    # Print the data received
    deadline_datetime = datetime.strptime(deadline, '%a, %d %b %Y %H:%M:%S %Z')
    deadline_mysql_format = deadline_datetime.strftime('%Y-%m-%d %H:%M:%S')
    try:
        # Connect to the database
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)

# Insert data into the "from_admin" table
        insert_query = "INSERT INTO from_admin (blood_bank_id, form_id, hospitalname, name, age, district, blood_group, quantity, address, reason, deadline, optional_details, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        insert_values = (district_to_code[district], form_id, hospital, name, age, district, blood_type, quantity, address, disease, deadline_mysql_format, details, 'pending')
        cursor.execute(insert_query, insert_values)

# Commit the insertion transaction
        connection.commit()

# Update the status in the "forms" table
        update_query = "UPDATE forms SET status = %s WHERE Admin_id = %s AND form_id = %s"
        update_values = ('Donated', Admin_id, form_id)
        cursor.execute(update_query, update_values)

# Commit the update transaction
        connection.commit()

# Close the cursor and the connection
        cursor.close()
        connection.close()

        
        response = {'message': 'Request submitted successfully!'}
    except mysql.connector.Error as error:
        print("Error while connecting to MySQL", error)
        response = {'message': 'Error occurred while submitting the request.'}

    return jsonify(response)




@app.route('/admin_req')
def admin_req():
    sample_data = fetchdata()
    return render_template('admin_recreq.html', requests=sample_data)


@app.route('/districts')
def get_districts():
    districts = ["Srikakulam", "Parvathipuram Manyam", "Vizianagaram", "Visakhapatnam", "Alluri Sitharama Raju", "Anakapalli)", "Kakinada", "East Godavari", "Dr. B. R. Ambedkar Konaseema", "Eluru", "West Godavari", "NTR", "Krishna", "Palnadu", "Guntur", "Bapatla", "Prakasam", "Sri Potti Sriramulu Nellore", "Kurnool", "Nandyal", "Anantapur", "Sri Sathya Sai", "YSR", "Annamayya", "Tirupati", "Chittoor"]
    return jsonify(districts)



@app.route('/update_data')
def update_data():
    if 'user_id' in session:
        sample_data = fetchdata()
        return jsonify(sample_data)
    else:
        return jsonify({'error': 'Admin_id not found in session'})


District=None



@app.route('/home')
def dashboard():
    return render_template('admin_home.html')

@app.route('/history')
def history():
    # Connect to MySQL database
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    print(Admin_id)
    # Example Admin_id

    # Execute SQL query to fetch history data
    cursor.execute("SELECT form_id, name, age, blood_group, quantity, hospitalname, address, reason, deadline, optional_details, district FROM forms WHERE admin_id = %s", (Admin_id,))
    history_data = cursor.fetchall()
    print(history_data)
    # Close cursor and connection
    cursor.close()
    conn.close()
    print(history_data)
    # Render history.html template with the fetched data
    return render_template('history.html', history_data=history_data)



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
            update_query_donations = "UPDATE login SET password = %s WHERE email = %s"
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


if __name__ == "__main__":
    app.run(debug=True)
