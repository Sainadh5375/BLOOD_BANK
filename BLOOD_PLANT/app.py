from os import abort
import random
import smtplib
from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import mysql.connector
import secrets
from datetime import datetime as dt

app = Flask(__name__,template_folder=r'C:\Users\saina\Downloads\SoftwareEngineerProject\BLOOD_PLANT')

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'sai@38293829',
    'database': 'database2',
    'auth_plugin': 'mysql_native_password'
}

app.secret_key = 'blood_bank'



def connect_to_database():
    return mysql.connector.connect(**db_config)

@app.route('/home.html', methods=['GET', 'POST'])
def home1():
    return render_template('home.html')

@app.route('/', methods=['GET', 'POST'])
def index():
    error_message = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT login_id FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        if user:
            session['user_id'] = user['login_id']
            return redirect(url_for('home1'))
        else:
            error_message = "Invalid email or password. Please try again."
    return render_template('login.html', error_message=error_message)

def get_available_slots(selected_date, appointment_time, selected_district):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM appointments WHERE appointment_date = %s AND district = %s and appointment_time=%s", (selected_date, selected_district, appointment_time))
        count = cursor.fetchone()[0]
        cursor.close()
        connection.close()
        return 10 - count
    except Exception as e:
        print("Error fetching available slots:", e)
        return 0

def generate_12_digit_code():
    return ''.join(secrets.choice('0123456789') for _ in range(12))

def code_exists12(code, cursor):
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE registration_id = %s", (code,))
    count = cursor.fetchone()[0]
    return count > 0

def generate_new_code(cursor):
    code = generate_12_digit_code()
    while code_exists12(code, cursor):
        code = generate_12_digit_code()
    return code
code_for_thankyou=None


def insert_appointment(appointment_date, appointment_time, selected_district, cursor):
    try:
        global code_for_thankyou
        registration_id = generate_new_code(cursor)
        cursor.execute("INSERT INTO appointments (login_id, registration_id, appointment_date, appointment_time, district) VALUES (%s, %s, %s, %s, %s)",
                       (session['user_id'], registration_id, appointment_date, appointment_time, selected_district))
        code_for_thankyou=registration_id
        return cursor.rowcount > 0
    
    except mysql.connector.Error as e:
        print("MySQL Error:", e.msg)
        return False, None
    except Exception as e:
        print("Error inserting appointment data:", e)
        return False, None



@app.route('/appointment.html', methods=['GET', 'POST'])
def appointment():
    if request.method == 'POST':
        appointment_date = request.form['appointment-date']
        appointment_time = request.form['appointment-time']
        selected_district = request.form['select-dist']
        
        # Store appointment details in session
        session['appointment_details'] = {
            'appointment_date': appointment_date,
            'appointment_time': appointment_time,
            'selected_district': selected_district
        }
        
        return redirect(url_for('donate'))  # Redirect to donation form
    
    return render_template('appointment.html')

name=None

# Modify the /donate.html route to insert both appointment and donation details into the database
@app.route('/donate.html', methods=['POST', 'GET'])
def donate():
    if request.method == 'POST':
        try:
            # Retrieve appointment details from session
            appointment_details = session.pop('appointment_details', None)
            if not appointment_details:
                return "Appointment details not found. Please try again."
            
            fname = request.form['fname']
            lname = request.form['lname']
            name=fname+lname
            print(name)
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
            diseases = request.form.get('Disease', '')  # If diseases not provided, set empty string
            
            # Now proceed with inserting both appointment and donation details into the database
            connection = connect_to_database()
            cursor = connection.cursor()
            
            if insert_appointment(appointment_details['appointment_date'], 
                                  appointment_details['appointment_time'], 
                                  appointment_details['selected_district'], cursor):
                
                # Generate a new registration ID if it already exists
                
                # Insert donation details into the database
                sql = "INSERT INTO donations (login_id, registration_id, first_name, last_name, dob, aadhar_no, email, phone_no, age, district, address, postal_code, occupation, gender, blood_group, blood_donated_before, diseases) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (session['user_id'], code_for_thankyou, fname, lname, dob, aadhar_no, email, phone_no, age, district, address, postal_code, occupation, gender, blood_group, blood_donated_before, diseases))
                
                connection.commit()
                cursor.close()
                connection.close()
                
                return redirect('/thankyou.html')
            else:
                return render_template('donate.html', message="Failed to insert appointment.")
        except mysql.connector.Error as e:
            print("MySQL Error:", e.msg)
            return "An error occurred while submitting the form."
        except Exception as e:
            print("Error:", e)
            return "An unexpected error occurred."

    return render_template('donate.html')

registration_id1=None
blood_type=None
@app.route('/add_blood.html', methods=['GET', 'POST'])
def add_blood():
    if request.method == 'POST':
        global registration_id1,blood_type
        registration_id = request.form['registration-id']
        
        registration_id1=registration_id
        print(registration_id1)
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT blood_group FROM donations WHERE registration_id = %s", (registration_id,))
        blood_type = cursor.fetchone()
        cursor.execute("SELECT * FROM donations WHERE registration_id = %s", (registration_id,))
        donation_data = cursor.fetchone()
        if donation_data:
            cursor.execute("SELECT appointment_date, appointment_time FROM appointments WHERE registration_id = %s", (registration_id,))
            appointment_data = cursor.fetchone()
            return render_template('add_blood.html', donation=donation_data, appointment=appointment_data)
        else:
            return "No donation found for the provided registration ID."
    return render_template('add_blood.html')  # Pass None if donation is not available


@app.route('/history.html')
def history():
    # Connect to the database
    conn = connect_to_database()
    cursor = conn.cursor()

    # Fetch distinct blood requests data from the database
    cursor.execute("SELECT DISTINCT(a.registration_id), a.appointment_date, "
                   "CONCAT(d.first_name, ' ', d.last_name) AS full_name, "
                   "d.gender, d.blood_group, d.status "
                   "FROM appointments a "
                   "INNER JOIN donations d ON a.login_id = d.login_id "
                   "WHERE a.login_id = %s", (session['user_id'],))
    appointments = cursor.fetchall()

    # Close the database connection
    conn.close()

    # Render the template with the fetched data
    return render_template('history.html', appointments=appointments)

    


@app.route('/thankyou.html')
def thankyou():
    global name,code_for_thankyou
    return render_template('thankyou.html',name=name,code=registration_id1)

blood_grp1=None

@app.route('/update_status', methods=['POST'])
def update_status():
    global blood_grp1
    global code_for_thankyou
    if request.method == 'POST':
        code_to_district = {
            "SRI01": "Srikakulam",
            "PM02": "Parvathipuram Manyam",
            "VZ03": "Vizianagaram",
            "VS04": "Visakhapatnam",
            "AS05": "Alluri Sitharama Raju",
            "AK06": "Anakapalli",
            "KK07": "Kakinada",
            "EG08": "East Godavari",
            "KN09": "Dr. B. R. Ambedkar Konaseema",
            "EL10": "Eluru",
            "WG11": "West Godavari",
            "NT12": "NTR",
            "KR13": "Krishna",
            "PL14": "Palnadu",
            "GU15": "Guntur",
            "BP16": "Bapatla",
            "PR17": "Prakasam",
            "NE18": "Sri Potti Sriramulu Nellore",
            "KU19": "Kurnool",
            "NN20": "Nandyal",
            "AN21": "Anantapur",
            "SS22": "Sri Sathya Sai",
            "CU23": "YSR",
            "AM24": "Annamayya",
            "TR25": "Tirupati",
            "CH26": "Chittoor"  # Corrected key
        }
        connection=connect_to_database()
        cursor=connection.cursor()
        cursor.execute("SELECT blood_group FROM donations WHERE registration_id = %s", (registration_id1,))
        blood_type = cursor.fetchone()
        print(code_to_district[session['user_id']])
        print(registration_id1)
        new_status = request.form['status']
        blood_unit = request.form.get('bloodunit')
        print(blood_unit)

        # Establish a database connection and create a cursor
        connection = connect_to_database()
        cursor = connection.cursor()

        blood_grp=None
        print(blood_type[0],blood_unit,registration_id1)
        if(blood_type[0]=='A+'):
            blood_grp='A_Positive'
        elif(blood_type[0]=='B+'):
            blood_grp='B_Positive'
        elif(blood_type[0]=='AB+'):
            blood_grp='AB_Positive'
        elif(blood_type[0]=='O+'):
            blood_grp='O_Positive'
        elif(blood_type[0]=='O-'):
            blood_grp='O_Negative'
        elif(blood_type[0]=='A-'):
            blood_grp='A_Negative'
        elif(blood_type[0]=='B-'):
            blood_grp='B_Negative'
        elif(blood_type[0]=='AB-'):
            blood_grp='AB_Negative'
        elif(blood_type[0]=='O-'):
            blood_grp='O_Negative'
        print(blood_grp)
        blood_grp1=blood_grp

        # Execute the necessary queries
        cursor.execute("SELECT " + blood_grp + " FROM bloodavailability WHERE District = %s", (code_to_district[session['user_id']],))
        users1 = cursor.fetchone()
        print(users1[0])
        new_data=users1[0]+int(blood_unit)
        cursor.execute("UPDATE bloodavailability SET "+ blood_grp +" = %s WHERE District = %s", (new_data,code_to_district[session['user_id']],))
        connection.commit()
        cursor.execute("UPDATE donations SET status = %s WHERE registration_id = %s", (new_status, registration_id1))
        connection.commit()

        # Close the cursor and the connection
        cursor.close()
        connection.close()

        return "Status updated successfully."

    return redirect('thankyou')




def fetchdata():
    global Admin_id
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT form_id, name, age, blood_group, quantity,gender, hospitalname, address, reason, deadline, optional_details, district FROM from_admin WHERE blood_bank_id = %s AND status = %s", (session['user_id'], 'pending'))
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
    cursor.close()
    connection.close()
    return sample_data



@app.route('/admin_req')
def admin_req():
    sample_data = fetchdata()
    return render_template('receving_request_admin.html', requests=sample_data)


@app.route('/districts')
def get_districts():
    districts = [    "Palasa", "Rajam", "Tekkali", "Amadalavalasa", "Ichapuram","Parvathipuram", "Salur", "Bobbili", "Gummalaxmipuram",
    # Vizianagaram
    "Vizianagaram", "Bobbili", "Parvathipuram", "Salur",
    # Visakhapatnam
    "Visakhapatnam", "Anakapalle", "Paderu", "Narsipatnam",
    # Alluri Sitharama Raju
    "Chintapalli", "G. Madugula", "Paderu", "Araku Valley",
    # Anakapalli
    "Anakapalle", "Chodavaram", "Yelamanchili", "Kasimkota",
    # Kakinada
    "Kakinada Rural", "Kakinada Urban", "Pithapuram", "Peddapuram",
    # East Godavari
    "Kakinada", "Rajahmundry", "Amalapuram", "Tuni",
    # Dr. B. R. Ambedkar Konaseema
    "Amalapuram", "Razole", "Mummidivaram", "Kothapeta",
    # Eluru
    "Eluru", "Tanuku", "Bhimavaram", "Tadepalligudem",
    # West Godavari
    "Eluru", "Bhimavaram", "Jangareddygudem", "Tadepalligudem",
    # NTR
    "Gudivada", "Nuzvid", "Vuyyuru", "Nandigama",
    # Krishna
    "Vijayawada", "Machilipatnam", "Gudivada", "Nandigama",
    # Palnadu
    "Narasaraopet", "Sattenapalle", "Chilakaluripet", "Vinukonda",
    # Guntur
    "Guntur", "Tenali", "Mangalagiri", "Narasaraopet",
    # Bapatla
    "Bapatla", "Ponnur", "Repalle", "Chirala",
    # Prakasam
    "Ongole", "Chirala", "Markapur", "Giddalur",
    # Sri Potti Sriramulu Nellore
    "Nellore", "Gudur", "Kavali", "Atmakur",
    # Kurnool
    "Kurnool", "Adoni", "Nandyal", "Yemmiganur",
    # Nandyal
    "Nandyal", "Adoni", "Kurnool", "Giddalur",
    # Anantapur
    "Anantapur", "Hindupur", "Dharmavaram", "Kadiri",
    "Puttaparthi", "Dharmavaram", "Kadiri", "Rayadurg",
    "Pulivendula", "Kadapa", "Proddatur", "Rajampet",
    # Annamayya
    "Rajampet", "Kadapa", "Proddatur", "Jammalamadugu",
    # Tirupati
    "Tirupati", "Chittoor", "Srikalahasti", "Madanapalle",
    # Chittoor
    "Chittoor", "Tirupati", "Madanapalle", "Srikalahasti"
]
    return jsonify(districts)


@app.route('/submit_request', methods=['POST'])
def submit_request():
    global registration_id1
    try:
        form_id = request.form.get('form_id')

        conn = connect_to_database()
        cursor = conn.cursor()
        print(form_id)
        
        code_to_district = {
    "SRI01": "Srikakulam",
    "PM02": "Parvathipuram Manyam",
    "VZ03": "Vizianagaram",
    "VS04": "Visakhapatnam",
    "AS05": "Alluri Sitharama Raju",
    "AK06": "Anakapalli",
    "KK07": "Kakinada",
    "EG08": "East Godavari",
    "KN09": "Dr. B. R. Ambedkar Konaseema",
    "EL10": "Eluru",
    "WG11": "West Godavari",
    "NT12": "NTR",
    "KR13": "Krishna",
    "PL14": "Palnadu",
    "GU15": "Guntur",
    "BP16": "Bapatla",
    "PR17": "Prakasam",
    "NE18": "Sri Potti Sriramulu Nellore",
    "KU19": "Kurnool",
    "NN20": "Nandyal",
    "AN21": "Anantapur",
    "SS22": "Sri Sathya Sai",
    "CU23": "YSR",
    "AM24": "Annamayya",
    "TR25": "Tirupati",
    "CH26": "Chittoor"  # Corrected key
    }   
        cursor.execute("SELECT blood_group FROM from_admin WHERE form_id = %s", (form_id,))
        blood_type = cursor.fetchone()
        print(blood_type[0])

        blood_grp=None
        if(blood_type[0]=='A+'):
            blood_grp='A_Positive'
        elif(blood_type[0]=='B+'):
            blood_grp='B_Positive'
        elif(blood_type[0]=='AB+'):
            blood_grp='AB_Positive'
        elif(blood_type[0]=='O+'):
            blood_grp='O_Positive'
        elif(blood_type[0]=='O-'):
            blood_grp='O_Negative'
        elif(blood_type[0]=='A-'):
            blood_grp='A_Negative'
        elif(blood_type[0]=='B-'):
            blood_grp='B_Negative'
        elif(blood_type[0]=='AB-'):
            blood_grp='AB_Negative'
        elif(blood_type[0]=='O-'):
            blood_grp='O_Negative'
        form_id = request.form.get('form_id')
        quantiy=int(request.form.get('quantity'))
# Connect to the database
        
        
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)
        
        sql_query = "SELECT " + blood_grp + " FROM bloodavailability WHERE District = %s"
        cursor.execute(sql_query, (code_to_district[session['user_id']],))
        users1 = cursor.fetchone()
        if(int(users1[blood_grp])>0):
            if(int(users1[blood_grp])-int(quantiy)>=0 and int(users1[blood_grp])>0):
                new_data=int(quantiy)-int(users1[blood_grp])
                cursor.execute("UPDATE bloodavailability SET "+ blood_grp +" = %s WHERE District = %s", (new_data,code_to_district[session['user_id']],))
                connection = connect_to_database()
                cursor = connection.cursor(dictionary=True)
                update_query_donations = "UPDATE donations SET status = %s WHERE registration_id = %s"
                update_values_donations = ('Donated', registration_id1)
                cursor.execute(update_query_donations, update_values_donations)

                update_query_from_admin = "UPDATE from_Admin SET status = %s WHERE blood_bank_id = %s AND form_id = %s"
                update_values_from_admin = ('Donated', session['user_id'], form_id)
                cursor.execute(update_query_from_admin, update_values_from_admin)
                connection.commit()
        else:
            return jsonify({'message':'blood is not sufficient iin this district'})
# Commit the changes
        connection.commit()

        cursor.close()
        connection.close()
        
        response = {'message': 'Request submitted successfully!'}
    except mysql.connector.Error as error:
        print("Error while connecting to MySQL", error)
        response = {'message': 'Error occurred while submitting the request.'}

    return jsonify(response)


@app.route('/update_data')
def update_data():
    if 'user_id' in session:
        sample_data = fetchdata()
        return jsonify(sample_data)
    else:
        return jsonify({'error': 'Admin_id not found in session'})


@app.route('/log_out')
def logout():
    return render_template('logout.html')





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
            update_query_donations = "UPDATE users SET password = %s WHERE email = %s"
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


if __name__ == "__main__":
    app.run(debug=True)