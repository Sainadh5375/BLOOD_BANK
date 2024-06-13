BLOOD_BANK

Overview
--------
The BLOOD_BANK project is a system designed to manage and facilitate blood donations. This repository contains the code and resources necessary to set up and run the BLOOD_BANK application using Flask.

Features
--------
- User registration and authentication
- Blood donation management
- Blood request management
- Donor and recipient matching
- Admin panel for managing users and donations

Requirements
------------
- Python 3.7+
- Flask 1.1+
- SQLite (default) or any other preferred database

Installation
------------
1. Clone the repository:
   git clone https://github.com/Sainadh5375/BLOOD_BANK.git
   cd BLOOD_BANK

2. Create a virtual environment:
   python -m venv env
   source env/bin/activate  # On Windows use `env\Scripts\activate`

3. Install dependencies:
   pip install -r requirements.txt

4. Set up the database:
   flask db init
   flask db migrate -m "Initial migration."
   flask db upgrade

5. Run the Flask application:
   flask run

Usage
-----
- Navigate to http://127.0.0.1:5000/ in your web browser.
- Register a new user or log in with the admin credentials.
- Explore the features of the BLOOD_BANK system.

Contributing
------------
If you would like to contribute to the project, please fork the repository and submit a pull request.
