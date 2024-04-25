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
	error = None
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

app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)
