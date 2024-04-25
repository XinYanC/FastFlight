# cd FOLDER
# python ./airlines_flask.py

from flask import Flask, render_template, request, url_for, redirect, session
import pymysql, pymysql.cursors

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                               user='root',
                               password='',
                               database='air_ticket_reservation_system')

#Define a route to hello function
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
	return render_template('login.html')

@app.route('/registrationToggle')
def registrationToggle():
	return render_template('registrationToggle.html')

@app.route('/customerRegistration')
def customerRegistration():
	return render_template('customerRegistration.html')

@app.route('/bookingAgentRegistration')
def bookingAgentRegistration():
	return render_template('bookingAgentRegistration.html')

@app.route('/staffRegistration')
def staffRegistration():
	return render_template('staffRegistration.html')

@app.route('/customerInterface')
def customerInterface():
	return render_template('customerInterface.html')

@app.route('/bookingAgentInterface')
def bookingAgentInterface():
	return render_template('bookingAgentInterface.html')

@app.route('/staffInterface')
def staffInterface():
	return render_template('staffInterface.html')


#Authenticates the login
@app.route('/loginSubmit', methods=['GET', 'POST'])
def loginSubmit():
	#grabs information from the forms
	username = request.form['login_email']
	password = request.form['login_password']
	user = request.form.get('user_type')

	#cursor used to send queries
	cursor = conn.cursor()

	if (user == "customer"):
		query = "SELECT * FROM customer WHERE cust_email = '{}' and c_password = '{}'"
		cursor.execute(query.format(username, password))
		data = cursor.fetchone()
	elif (user == "booking_agent"):
		query = "SELECT * FROM booking_agent WHERE booking_agent_email = '{}' and ba_password = '{}'"
		cursor.execute(query.format(username, password))
		data = cursor.fetchone()
	elif (user == "airline_staff"):
		query = "SELECT * FROM airline_staff WHERE username = '{}' and s_password = '{}'"
		cursor.execute(query.format(username, password))
		data = cursor.fetchone()
	# #executes query
	# query = "SELECT * FROM user WHERE username = '{}' and password = '{}'"
	# cursor.execute(query.format(username, password))
	# #stores the results in a variable
	# data = cursor.fetchone()
	# #use fetchall() if you are expecting more than 1 data row


	cursor.close()
	loginError = None
	if(data):
		#creates a session for the the user
		#session is a built in
		session['username'] = username
		if (user == "customer"):
			return redirect(url_for('customerInterface'))
		elif (user == "booking_agent"):
			return redirect(url_for('bookingAgentInterface'))
		elif (user == "airline_staff"):
			return redirect(url_for('staffInterface'))
	else:
		#returns an error message to the html page
		loginError = 'Invalid login or username'
		return render_template('login.html', loginError=loginError)
	

#Authenticates the register
@app.route('/customerRegister', methods=['GET', 'POST'])
def customerRegister():
	#grabs information from the forms
	cust_email = request.form['cust_email']
	cust_fname = request.form['cust_fname']
	cust_lname = request.form['cust_lname']
	cust_name = cust_fname + ' ' + cust_lname
	cust_password = request.form['cust_password']
	cust_bnum = request.form['cust_bnum']
	cust_street = request.form['cust_street']
	cust_city = request.form['cust_city']
	cust_state = request.form.get('cust_state')
	cust_number = request.form['cust_number']
	cust_passNum = request.form['cust_passNum']
	cust_passExp = request.form['cust_passExp']
	cust_passCty = request.form.get('cust_passCty')
	cust_dob = request.form['cust_dob']


	#cursor used to send queries
	cursor = conn.cursor()
	#executes query
	query = "SELECT * FROM customer WHERE cust_email = '{}'"
	cursor.execute(query.format(cust_email))
	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	registrationError = None
	if(data):
		#If the previous query returns data, then user exists
		registrationError = "This user already exists"
		return render_template('register.html', registrationError = registrationError)
	else:
		ins = "INSERT INTO customer VALUES('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')"
		cursor.execute(ins.format(cust_email, cust_name, cust_password, cust_bnum, cust_street, cust_city, cust_state, cust_number, cust_passNum, cust_passExp, cust_passCty, cust_dob))
		conn.commit()
		cursor.close()
		registerSuccess = "Registration successful! Login in now"
		return render_template('login.html', registerSuccess = registerSuccess)

@app.route('/bookingAgentRegister', methods=['GET', 'POST'])
def bookingAgentRegister():
	#grabs information from the forms
	bagent_email = request.form['bagent_email']
	bagent_password = request.form['bagent_password']
	bagent_id = request.form['bagent_id']

	#cursor used to send queries
	cursor = conn.cursor()
	#executes query
	query = "SELECT * FROM booking_agent WHERE booking_agent_email = '{}'"
	cursor.execute(query.format(bagent_email))
	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	registrationError = None
	if(data):
		#If the previous query returns data, then user exists
		registrationError = "This user already exists"
		return render_template('register.html', registrationError = registrationError)
	else:
		ins = "INSERT INTO booking_agent VALUES('{}', '{}', '{}')"
		cursor.execute(ins.format(bagent_email,bagent_password, bagent_id))
		conn.commit()
		cursor.close()
		registerSuccess = "Registration successful! Login in now"
		return render_template('login.html', registerSuccess = registerSuccess)

@app.route('/staffRegister', methods=['GET', 'POST'])
def staffRegister():
	#grabs information from the forms
	staff_user = request.form['staff_user']
	staff_password = request.form['staff_password']
	staff_fname = request.form['staff_fname']
	staff_lname = request.form['staff_lname']
	staff_dob = request.form['staff_dob']
	staff_airline = request.form.get('staff_airline')

	#cursor used to send queries
	cursor = conn.cursor()
	#executes query
	query = "SELECT * FROM airline_staff WHERE username = '{}'"
	cursor.execute(query.format(staff_user))
	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	registrationError = None
	if(data):
		#If the previous query returns data, then user exists
		registrationError = "This user already exists"
		return render_template('register.html', registrationError = registrationError)
	else:
		ins = "INSERT INTO airline_staff VALUES('{}', '{}', '{}', '{}', '{}', '{}')"
		cursor.execute(ins.format(staff_user, staff_password, staff_fname, staff_lname, staff_dob, staff_airline))
		conn.commit()
		cursor.close()
		registerSuccess = "Registration successful! Login in now"
		return render_template('login.html', registerSuccess = registerSuccess)




app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)
