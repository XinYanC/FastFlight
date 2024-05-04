# cd FOLDER
# python ./airlines_flask.py

from flask import Flask, render_template, request, url_for, redirect, session, jsonify
import pymysql, pymysql.cursors
import hashlib
from pymysql import NULL
from datetime import datetime, timedelta
from collections import defaultdict
import calendar
import json
from dateutil.relativedelta import relativedelta


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
	if ('username' in session):
		if 'customer' in session:
			cursor = conn.cursor()
			cursor.execute("SELECT c_name FROM customer WHERE cust_email = %s", session['username'])
			c_name = cursor.fetchone()[0]
			cursor.close()

			# Split the full name into words
			name_parts = c_name.split()
			# Join all but the last word
			first_name = ' '.join(name_parts[:-1])
			
			return redirect(url_for('customerInterface', cust_name=first_name))
		elif 'booking_agent' in session:
			cursor = conn.cursor()
			cursor.execute("SELECT booking_agent_id FROM booking_agent WHERE booking_agent_email = %s", session['username'])
			booking_agent_id = cursor.fetchone()[0]
			cursor.close()

			return redirect(url_for('bookingAgentInterface', booking_agent_id=booking_agent_id))
		elif 'airline_staff' in session:
			cursor = conn.cursor()
			cursor.execute("SELECT first_name FROM airline_staff WHERE username = %s", session['username'])
			first_name = cursor.fetchone()[0]
			cursor.close()

			return redirect(url_for('staffInterface', staff_name=first_name))
	return render_template('index.html')


@app.route('/login')
def login():
	# Retrieve the logOutSuccess message from the URL query parameters
    logOutSuccess = request.args.get('logOutSuccess', None)
    if logOutSuccess:
        logOutSuccess = "Logged out successfully!"
        # Render the login.html template with the logOutSuccess message
        return render_template('login.html', logOutSuccess=logOutSuccess)
    else:
        # Render the login.html template without passing logOutSuccess
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
	cust_name = request.args.get('cust_name', 'again')
	return render_template('customerInterface.html', cust_name=cust_name)

@app.route('/bookingAgentInterface')
def bookingAgentInterface():
	booking_agent_id = request.args.get('booking_agent_id', 'again')
	return render_template('bookingAgentInterface.html', booking_agent_id=booking_agent_id)

@app.route('/staffInterface')
def staffInterface():
	staff_name = request.args.get('staff_name', 'again')  # Get staff_name from query parameter
	staff_operator = False
	if 'operator' in session:
		staff_operator = True
	if 'admin' in session:
		staff_admin = True

	return render_template('staffInterface.html', staff_name=staff_name, staff_operator=staff_operator, staff_admin=staff_admin)

@app.route('/flightResult')
def flightResult():
	return render_template('flightResult.html')

@app.route('/successfulBooking')
def successfulBooking():
	return render_template('successfulBooking.html')

@app.route('/searchFlights')
def searchFlights():
	# flight_sql = """
	# 				SELECT 
	# 					airline_name, 
	# 					flight_num, 
	# 					TIME_FORMAT(departure_time, '%H:%i') AS formatted_departure_time, 
	# 					TIME_FORMAT(arrival_time, '%H:%i') AS formatted_arrival_time,  
	# 					price 
	# 				FROM 
	# 					flight 
	# 				WHERE 
	# 					flight_status = 'upcoming'
	# 				ORDER BY 
	# 					departure_time
	# 			"""
	if 'booking_agent' in session:
		flight_sql = """
						SELECT 
							f.airline_name, 
							f.flight_num, 
							TIME_FORMAT(f.departure_time, '%%H:%%i') AS formatted_departure_time, 
							TIME_FORMAT(f.arrival_time, '%%H:%%i') AS formatted_arrival_time, 
							f.price,
							DATE(f.departure_time) AS formatted_departure_date,
							a.total_seats,
							(
								SELECT COUNT(*)
								FROM ticket t
								WHERE t.flight_num = f.flight_num
							) AS booked_seats
						FROM 
							flight f
						INNER JOIN 
							airplane a ON f.airplane_id = a.airplane_id
						INNER JOIN
							works_for w ON f.airline_name = w.airline_name
						WHERE 
							flight_status = 'upcoming'
							AND w.booking_agent_email = %s
						HAVING 
							booked_seats < a.total_seats
						ORDER BY 
							formatted_departure_date, formatted_departure_time;
					"""
	elif 'airline_staff' in session:
		flight_sql = """
						SELECT 
							f.airline_name, 
							f.flight_num, 
							TIME_FORMAT(f.departure_time, '%%H:%%i') AS formatted_departure_time, 
							TIME_FORMAT(f.arrival_time, '%%H:%%i') AS formatted_arrival_time, 
							f.price,
							DATE(f.departure_time) AS formatted_departure_date,
							a.total_seats,
							(
								SELECT COUNT(*)
								FROM ticket t
								WHERE t.flight_num = f.flight_num
							) AS booked_seats
						FROM 
							flight f
						INNER JOIN 
							airplane a ON f.airplane_id = a.airplane_id
						INNER JOIN
							airline_staff astaff ON f.airline_name = astaff.airline_name
						WHERE 
							f.flight_status = 'upcoming'
							AND astaff.username = %s
						HAVING 
							booked_seats < a.total_seats
						ORDER BY 
							formatted_departure_date, formatted_departure_time;
					"""

		# flight_sql = """
		# 				SELECT 
		# 					f.airline_name, 
		# 					f.flight_num, 
		# 					TIME_FORMAT(f.departure_time, '%%H:%%i') AS formatted_departure_time, 
		# 					TIME_FORMAT(f.arrival_time, '%%H:%%i') AS formatted_arrival_time, 
		# 					f.price,
		# 					DATE(f.departure_time) AS formatted_departure_date
		# 				FROM 
		# 					flight f
		# 				INNER JOIN 
		# 					airline_staff s ON f.airline_name = s.airline_name
		# 				INNER JOIN 
		# 					ticket t ON f.flight_num = t.flight_num
		# 				WHERE 
		# 					s.username = %s
		# 					AND f.departure_time >= %s
		# 					AND f.departure_time < %s
		# 					AND f.flight_status = 'upcoming'
		# 				ORDER BY 
		# 					formatted_departure_date, formatted_departure_time;
		# 			"""
	else:
		flight_sql = """
						SELECT 
							f.airline_name,
							f.flight_num,
							TIME_FORMAT(f.departure_time, '%H:%i') AS formatted_departure_time,
							TIME_FORMAT(f.arrival_time, '%H:%i') AS formatted_arrival_time,
							f.price,
							DATE(f.departure_time) AS formatted_departure_date,
							a.total_seats,
							(
								SELECT COUNT(*)
								FROM ticket t
								WHERE t.flight_num = f.flight_num
							) AS booked_seats
						FROM 
							flight f
						INNER JOIN 
							airplane a ON f.airplane_id = a.airplane_id
						WHERE 
							flight_status = 'upcoming'
						HAVING 
							booked_seats < a.total_seats
						ORDER BY 
							formatted_departure_date, formatted_departure_time;
					"""

	try:
		# Execute the SQL query
		with conn.cursor() as cursor:
			if 'booking_agent' in session:
				cursor.execute(flight_sql, session['username'])
			elif 'airline_staff' in session:
				cursor.execute(flight_sql, session['username'])
			else:
				cursor.execute(flight_sql)
			flights = cursor.fetchall()
			if flights:
				flights_heading = 'Upcoming Flights'
			else:
				flights_heading = 'No Upcoming Flights'
			return render_template('searchFlights.html', flights_heading=flights_heading, sourcePlaceholder='From airport/city...', destPlaceholder='To airport/city...', datePlaceholder='Select date...', flights=flights, flightDepDate=True)
	finally:
		conn.close()

@app.route('/stats')
def stats():
	# days = request.form['timeRange']
	if 'booking_agent' in session:
		now = datetime.now()
		past_thirty = now - timedelta(days=30)
		total_amount = 0

		cursor = conn.cursor()
		cursor.execute("SELECT booking_agent_id FROM booking_agent WHERE booking_agent_email = %s", session['username'])
		booking_agent_id = cursor.fetchone()[0]
		cursor.close()

		cursor = conn.cursor()
		cursor.execute("""
							SELECT IFNULL(SUM(f.price * .1), 0) AS total_amount, 
								IFNULL(AVG(f.price * .1), 0) AS avg_amount, 
								COUNT(*) AS num_flights
							FROM ticket t
							INNER JOIN flight f ON t.flight_num = f.flight_num
							WHERE t.booking_agent_id = %s
							AND t.booking_date >= %s;
						""", (booking_agent_id, past_thirty))
		ba_stats = cursor.fetchall()
		cursor.close()

		past_thirty_days = [now - timedelta(days=i) for i in range(1, 30)]
		day_labels = [day.strftime("%m/%d") for day in past_thirty_days]
		day_labels.reverse()

		daily_commission = []

		cursor = conn.cursor()
		for day in past_thirty_days:
			cursor.execute("""
				SELECT SUM(f.price * 0.1) AS commission
				FROM ticket t
				INNER JOIN flight f ON t.flight_num = f.flight_num
				WHERE t.booking_agent_id = %s
					AND DATE(t.booking_date) = %s;
			""", (booking_agent_id, day))
			amount = cursor.fetchone()
			if (amount):
				daily_commission.append(amount[0])
			else:
				daily_commission.append(0)

		cursor.close()

		daily_commission.reverse()
		# Convert Decimal objects to floating-point numbers
		daily_commission = [float(amount) if amount else 0.0 for amount in daily_commission]

		# Convert the lists to JSON format
		day_labels_json = json.dumps(day_labels)
		daily_commission_json = json.dumps(daily_commission)
		
		return render_template('stats.html', stats_heading='My Commissions', total_amount=ba_stats, now=now, past_year=past_thirty, monthly_spending=daily_commission_json, month_labels=day_labels_json, stat_type='ba')
	elif 'customer' in session:
		now = datetime.now()
		past_year = now - timedelta(days=365)
		total_amount = 0

		cursor = conn.cursor()
		cursor.execute("""
							SELECT SUM(f.price) AS total_amount
							FROM ticket t
							INNER JOIN flight f ON t.flight_num = f.flight_num
							WHERE t.cust_email = %s
								AND t.booking_date >= %s;
						""", (session['username'], past_year))
		total_amount = cursor.fetchall()[0]  # Fetch the total amount
		cursor.close()

		past_six_months = [now - timedelta(days=30*i) for i in range(1, 7)]
		month_labels = [month.strftime("%B %Y") for month in past_six_months]
		month_labels.reverse()

		monthly_spending = []

		cursor = conn.cursor()
		for month in past_six_months:
			start_of_month = month.replace(day=1)
			end_of_month = month.replace(day=calendar.monthrange(month.year, month.month)[1])

			cursor.execute("""
				SELECT IFNULL(SUM(f.price), 0) AS total_amount
				FROM ticket t
				INNER JOIN flight f ON t.flight_num = f.flight_num
				WHERE t.cust_email = %s
					AND DATE(t.booking_date) BETWEEN DATE(%s) AND DATE(%s);
			""", (session['username'], start_of_month, end_of_month))
			amount = cursor.fetchone()[0]
			if (amount):
				monthly_spending.append(amount)
			else:
				monthly_spending.append(0)

		cursor.close()

		monthly_spending.reverse()
		# Convert Decimal objects to floating-point numbers
		monthly_spending = [float(amount) if amount else 0.0 for amount in monthly_spending]

		# Convert the lists to JSON format
		month_labels_json = json.dumps(month_labels)
		monthly_spending_json = json.dumps(monthly_spending)

		return render_template('stats.html', stats_heading='My Spendings', total_amount=total_amount, now=now, past_year=past_year, monthly_spending=monthly_spending_json, month_labels=month_labels_json, stat_type='cust')
	return render_template('stats.html')

@app.route('/custStatRange', methods=['GET', 'POST'])
def custStatRange():
	searchFromDate = request.form['searchFromDate']
	searchToDate = request.form['searchToDate']

	if 'booking_agent' in session:
		# now = datetime.now()
		# past_thirty = now - timedelta(days=30)
		total_amount = 0

		from_date = datetime.strptime(searchFromDate, "%Y-%m-%d")
		to_date = datetime.strptime(searchToDate, "%Y-%m-%d")

		days_between = (to_date - from_date).days 
		date_range = [to_date - timedelta(days=i) for i in range(days_between)]
		date_range.reverse()

		day_labels = [day.strftime("%m/%d") for day in date_range]

		daily_commission = []

		cursor = conn.cursor()
		cursor.execute("SELECT booking_agent_id FROM booking_agent WHERE booking_agent_email = %s", session['username'])
		booking_agent_id = cursor.fetchone()[0]
		cursor.close()

		cursor = conn.cursor()
		cursor.execute("""
							SELECT IFNULL(SUM(f.price * .1), 0) AS total_amount, 
								IFNULL(AVG(f.price * .1), 0) AS avg_amount, 
								COUNT(*) AS num_flights
							FROM ticket t
							INNER JOIN flight f ON t.flight_num = f.flight_num
							WHERE t.booking_agent_id = %s
								AND DATE(t.booking_date) BETWEEN DATE(%s) AND DATE(%s);
						""", (booking_agent_id, from_date, to_date))
		ba_stats = cursor.fetchall()
		cursor.close()

		cursor = conn.cursor()
		for day in date_range:
			cursor.execute("""
				SELECT SUM(f.price * 0.1) AS commission
				FROM ticket t
				INNER JOIN flight f ON t.flight_num = f.flight_num
				WHERE t.booking_agent_id = %s
					AND DATE(t.booking_date) = %s;
			""", (booking_agent_id, day))
			amount = cursor.fetchone()
			if (amount):
				daily_commission.append(amount[0])
			else:
				daily_commission.append(0)

		cursor.close()

		daily_commission.reverse()
		# Convert Decimal objects to floating-point numbers
		daily_commission = [float(amount) if amount else 0.0 for amount in daily_commission]

		# Convert the lists to JSON format
		day_labels_json = json.dumps(day_labels)
		daily_commission_json = json.dumps(daily_commission)
		
		return render_template('stats.html', stats_heading='My Commissions', total_amount=ba_stats, now=to_date, past_year=from_date, monthly_spending=daily_commission_json, month_labels=day_labels_json, stat_type='ba')
	elif 'customer' in session:
		now = datetime.now()
		# past_year = now - timedelta(days=365)
		total_amount = 0

		from_date = datetime.strptime(searchFromDate, "%Y-%m-%d")
		to_date = datetime.strptime(searchToDate, "%Y-%m-%d")

		months_between = [
			from_date + relativedelta(months=i) for i in range((to_date.year - from_date.year) * 12 + to_date.month - from_date.month + 1)
		]
		months_between.reverse()  # Reverse the list to have the oldest month first

		month_labels = [month.strftime("%B %Y") for month in months_between]

		monthly_spending = []

		cursor = conn.cursor()
		cursor.execute("""
							SELECT IFNULL(SUM(f.price), 0) AS total_amount
							FROM ticket t
							INNER JOIN flight f ON t.flight_num = f.flight_num
							WHERE t.cust_email = %s
								AND DATE(t.booking_date) BETWEEN DATE(%s) AND DATE(%s);
						""", (session['username'], from_date, to_date))
		total_amount = cursor.fetchall()[0]  # Fetch the total amount
		cursor.close()

		cursor = conn.cursor()
		for month in months_between:
			start_of_month = month.replace(day=1)
			end_of_month = month.replace(day=calendar.monthrange(month.year, month.month)[1])

			cursor.execute("""
				SELECT SUM(f.price) AS total_amount
				FROM ticket t
				INNER JOIN flight f ON t.flight_num = f.flight_num
				WHERE t.cust_email = %s
					AND DATE(t.booking_date) BETWEEN DATE(%s) AND DATE(%s);
			""", (session['username'], start_of_month, end_of_month))
			amount = cursor.fetchone()[0]
			if amount:
				monthly_spending.append(amount)
			else:
				monthly_spending.append(0)

		cursor.close()

		monthly_spending.reverse()
		# Convert Decimal objects to floating-point numbers
		monthly_spending = [float(amount) if amount else 0.0 for amount in monthly_spending]

		# Convert the lists to JSON format
		month_labels_json = json.dumps(month_labels)
		monthly_spending_json = json.dumps(monthly_spending)

		return render_template('stats.html', stats_heading='My Spendings', total_amount=total_amount, now=to_date, past_year=from_date, monthly_spending=monthly_spending_json, month_labels=month_labels_json, stat_type='cust')
	return render_template('stats.html')

@app.route('/viewFlights')
def viewFlights():
	current_date = datetime.now().date()
	end_date = current_date + timedelta(days=30)
	# flight_sql = """
	# 				SELECT 
	# 					airline_name, 
	# 					flight_num, 
	# 					TIME_FORMAT(departure_time, '%H:%i') AS formatted_departure_time, 
	# 					TIME_FORMAT(arrival_time, '%H:%i') AS formatted_arrival_time,  
	# 					price 
	# 				FROM 
	# 					flight 
	# 				WHERE 
	# 					flight_status = 'upcoming'
	# 				ORDER BY 
	# 					departure_time
	# 			"""
	if 'booking_agent' in session:
		flight_sql = """
						SELECT 
							f.airline_name, 
							f.flight_num, 
							TIME_FORMAT(f.departure_time, '%%H:%%i') AS formatted_departure_time, 
							TIME_FORMAT(f.arrival_time, '%%H:%%i') AS formatted_arrival_time, 
							f.price,
							DATE(f.departure_time) AS formatted_departure_date,
							c.c_name
						FROM 
							flight f
						INNER JOIN 
							ticket t ON f.flight_num = t.flight_num
						INNER JOIN 
							booking_agent b ON t.booking_agent_id = b.booking_agent_id
						LEFT JOIN 
							customer c ON t.cust_email = c.cust_email
						WHERE 
							b.booking_agent_email = %s
						ORDER BY 
							formatted_departure_date, formatted_departure_time;
					"""
	elif 'customer' in session:
		flight_sql = """
						SELECT 
							f.airline_name, 
							f.flight_num, 
							TIME_FORMAT(f.departure_time, '%%H:%%i') AS formatted_departure_time, 
							TIME_FORMAT(f.arrival_time, '%%H:%%i') AS formatted_arrival_time, 
							f.price,
							DATE(f.departure_time) AS formatted_departure_date
						FROM 
							flight f
						INNER JOIN 
							ticket t ON f.flight_num = t.flight_num
						WHERE 
							t.cust_email = %s
						ORDER BY 
							formatted_departure_date, formatted_departure_time;
					"""
	elif 'airline_staff' in session:
		flight_sql = """
						SELECT 
							f.airline_name, 
							f.flight_num, 
							TIME_FORMAT(f.departure_time, '%%H:%%i') AS formatted_departure_time, 
							TIME_FORMAT(f.arrival_time, '%%H:%%i') AS formatted_arrival_time, 
							f.price,
							DATE(f.departure_time) AS formatted_departure_date
						FROM 
							flight f
						INNER JOIN 
							airline_staff s ON f.airline_name = s.airline_name
						INNER JOIN 
							ticket t ON f.flight_num = t.flight_num
						WHERE 
							s.username = %s
							AND f.departure_time >= %s
							AND f.departure_time < %s
							AND f.flight_status = 'upcoming'
						ORDER BY 
							formatted_departure_date, formatted_departure_time;
					"""

	try:
		# Execute the SQL query
		with conn.cursor() as cursor:
			if 'airline_staff' in session: 
				cursor.execute(flight_sql, (session['username'], current_date, end_date))
			else:
				cursor.execute(flight_sql, session['username'])
			flights = cursor.fetchall()
			if (flights):
				return render_template('viewFlights.html', flights_heading='View Upcoming Flights', sourcePlaceholder='From airport/city...', destPlaceholder='To airport/city...', datePlaceholder='Select date...', flights=flights, flightDepDate=True)
			else:
				return render_template('viewFlights.html', flights_heading='No Upcoming Flights', sourcePlaceholder='From airport/city...', destPlaceholder='To airport/city...', datePlaceholder='Select date...')
	finally:
        # Close the database connection
		conn.close()


#Authenticates the login
@app.route('/loginSubmit', methods=['GET', 'POST'])
def loginSubmit():
	#grabs information from the forms
	username = request.form['login_email']
	password = request.form['login_password']
	user = request.form.get('user_type')

	# hash the password using MD5
	hashedPassword = hashlib.md5(password.encode()).hexdigest()

	#cursor used to send queries
	cursor = conn.cursor()

	data = None

	if (user == "customer"):
		session['customer'] = True
		query = "SELECT * FROM customer WHERE cust_email = '{}' and c_password = '{}'"
		cursor.execute(query.format(username, hashedPassword))
		data = cursor.fetchone()
	elif (user == "booking_agent"):
		session['booking_agent'] = True
		query = "SELECT * FROM booking_agent WHERE booking_agent_email = '{}' and ba_password = '{}'"
		cursor.execute(query.format(username, hashedPassword))
		data = cursor.fetchone()
	elif (user == "airline_staff"):
		session['airline_staff'] = True
		query = "SELECT * FROM airline_staff WHERE username = '{}' and s_password = '{}'"
		cursor.execute(query.format(username, hashedPassword))
		data = cursor.fetchone()
	# #executes query
	# query = "SELECT * FROM user WHERE username = '{}' and password = '{}'"
	# cursor.execute(query.format(username, password))
	# #stores the results in a variable
	# data = cursor.fetchone()
	# #use fetchall() if you are expecting more than 1 data row
	cursor.close()

	cursor = conn.cursor()
	if 'airline_staff' in session:
		query = "SELECT permission FROM permission WHERE username = %s"
		cursor.execute(query, (username,))
		staff_status = cursor.fetchall()
		for status in staff_status:
			if status[0] == 'admin':  # Assuming 'admin' is stored as a string in the database
				session['admin'] = True
				print('Admin:', session['admin'])
			if status[0] == 'operator':  # Assuming 'operator' is stored as a string in the database
				session['operator'] = True
				print('Operator:', session['operator'])
	cursor.close()

	loginError = None

	if(data):
		#creates a session for the the user
		#session is a built in
		session['username'] = username
		if (user == "customer"):
			cursor = conn.cursor()
			cursor.execute("SELECT c_name FROM customer WHERE cust_email = %s", username)
			c_name = cursor.fetchone()[0]
			cursor.close()

			# Split the full name into words
			name_parts = c_name.split()
			# Join all but the last word
			first_name = ' '.join(name_parts[:-1])
			
			return redirect(url_for('customerInterface', cust_name=first_name))
		elif (user == "booking_agent"):
			cursor = conn.cursor()
			cursor.execute("SELECT booking_agent_id FROM booking_agent WHERE booking_agent_email = %s", username)
			booking_agent_id = cursor.fetchone()[0]
			cursor.close()

			return redirect(url_for('bookingAgentInterface', booking_agent_id=booking_agent_id))
		elif (user == "airline_staff"):
			cursor = conn.cursor()
			cursor.execute("SELECT first_name FROM airline_staff WHERE username = %s", username)
			first_name = cursor.fetchone()[0]
			print(first_name)
			cursor.close()

			return redirect(url_for('staffInterface', staff_name=first_name))
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

	hashedPassword = hashlib.md5(cust_password.encode()).hexdigest()

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
		return render_template('customerRegistration.html', registrationError = registrationError)
	else:
		ins = "INSERT INTO customer VALUES('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')"
		cursor.execute(ins.format(cust_email, cust_name, hashedPassword, cust_bnum, cust_street, cust_city, cust_state, cust_number, cust_passNum, cust_passExp, cust_passCty, cust_dob))
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

	hashedPassword = hashlib.md5(bagent_password.encode()).hexdigest()

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
		return render_template('bookingAgentRegistration.html', registrationError = registrationError)
	else:
		ins = "INSERT INTO booking_agent VALUES('{}', '{}', '{}')"
		cursor.execute(ins.format(bagent_email, hashedPassword, bagent_id))
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

	hashedPassword = hashlib.md5(staff_password.encode()).hexdigest()

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
		return render_template('staffRegistration.html', registrationError = registrationError)
	else:
		ins = "INSERT INTO airline_staff VALUES('{}', '{}', '{}', '{}', '{}', '{}')"
		cursor.execute(ins.format(staff_user, hashedPassword, staff_fname, staff_lname, staff_dob, staff_airline))
		conn.commit()
		cursor.close()
		registerSuccess = "Registration successful! Login in now"
		return render_template('login.html', registerSuccess = registerSuccess)

@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    # Redirect to the login page with the success message
    return redirect('/login?logOutSuccess=Logged out successfully!')

@app.route('/get_airport_suggestions', methods=['POST'])
def get_airport_suggestions():
    print("Function get_airport_suggestions() called")  # Add this line for debugging
    search_query = request.form['searchQuery']
    suggestions = []

    if search_query:
        try:
            with conn.cursor() as cursor:
                sql = "SELECT airport_name FROM airport WHERE airport_name LIKE %s"
                cursor.execute(sql, (search_query + '%',))
                suggestions = [row['airport_name'] for row in cursor.fetchall()]
        except Exception as e:
            print("Error fetching airport suggestions:", e)

    return jsonify(suggestions)

@app.route('/searchFlightsResults', methods=['POST'])
def searchFlightsResults():
	source_search = request.form['sourceSearch'].upper()  
	destination_search = request.form['destinationSearch'].upper()  
	search_date = request.form['searchDate']

	print("Source Search:", source_search)
	print("Destination Search:", destination_search)
	print("Search Date:", search_date)

	# Function to search for airport by multi-word city names
	# def search_airport(search_term):
	#     words = search_term.split()  # Split input into words
	#     airport_names = []
	#     # Search for each word individually
	#     with conn.cursor() as airport_cursor:
	#         for word in words:
	#             airport_sql = "SELECT airport_name FROM airport WHERE UPPER(airport_name) LIKE %s OR UPPER(airport_city) LIKE %s"
	#             airport_cursor.execute(airport_sql, ('%' + word.upper() + '%', '%' + word.upper() + '%'))
	#             result = airport_cursor.fetchone()
	#             if result:
	#                 airport_names.append(result[0])
	#     return airport_names

	def search_airport(search_term):
		with conn.cursor() as airport_cursor:
			airport_sql = "SELECT airport_name FROM airport WHERE UPPER(airport_city) = %s"
			airport_cursor.execute(airport_sql, search_term)
			results = airport_cursor.fetchall()
			airports = [result[0] if isinstance(result, tuple) else result['airport_name'] for result in results]
			print("Airports in", search_term, ":", airports)
			return airports

	# source_airports = search_airport(source_search)
	# destination_airports = search_airport(destination_search)

	# If source_search is not a city, set source_airports to source_search
	if not search_airport(source_search):
		source_airports = [source_search]
	else:
		source_airports = search_airport(source_search)

	# If destination_search is not a city, set destination_airports to destination_search
	if not search_airport(destination_search):
		destination_airports = [destination_search]
	else:
		destination_airports = search_airport(destination_search)


	if source_airports and destination_airports:
		# Execute SQL query to find flights
		with conn.cursor() as flight_cursor:
			# flight_sql = "SELECT airline_name, flight_num, TIME(departure_time), TIME(arrival_time), price FROM flight WHERE UPPER(depart_airport_name) IN %s AND UPPER(arrival_airport_name) IN %s AND DATE(departure_time) = %s AND flight_status = 'upcoming'"
			# flight_sql="""
			# 				SELECT 
			# 					airline_name, 
			# 					flight_num, 
			# 					TIME_FORMAT(departure_time, '%%H:%%i') AS formatted_departure_time, 
			# 					TIME_FORMAT(arrival_time, '%%H:%%i') AS formatted_arrival_time, 
			# 					price 
			# 				FROM 
			# 					flight 
			# 				WHERE 
			# 					UPPER(depart_airport_name) IN %s 
			# 					AND UPPER(arrival_airport_name) IN %s 
			# 					AND DATE(departure_time) = %s 
			# 					AND flight_status = 'upcoming'
			# 				ORDER BY 
			# 					price
			# 				"""
			
			if 'booking_agent' in session:
				flight_sql = """
								SELECT 
									f.airline_name, 
									f.flight_num, 
									TIME_FORMAT(f.departure_time, '%%H:%%i') AS formatted_departure_time, 
									TIME_FORMAT(f.arrival_time, '%%H:%%i') AS formatted_arrival_time, 
									f.price,
									DATE(f.departure_time) AS formatted_departure_date,
									a.total_seats,
									(
										SELECT COUNT(*)
										FROM ticket t
										WHERE t.flight_num = f.flight_num
									) AS booked_seats
								FROM 
									flight f
								INNER JOIN 
									airplane a ON f.airplane_id = a.airplane_id
								INNER JOIN
									works_for w ON f.airline_name = w.airline_name
								WHERE 
									UPPER(depart_airport_name) IN %s 
									AND UPPER(arrival_airport_name) IN %s 
									AND DATE(departure_time) = %s 
									AND flight_status = 'upcoming'
									AND w.booking_agent_email = %s
								HAVING 
									booked_seats < a.total_seats
								ORDER BY 
									price;
							"""
				flight_cursor.execute(flight_sql, (tuple(source_airports), tuple(destination_airports), search_date, session['username']))
			elif 'airline_staff' in session:
				flight_sql = """
								SELECT 
									f.airline_name, 
									f.flight_num, 
									TIME_FORMAT(f.departure_time, '%%H:%%i') AS formatted_departure_time, 
									TIME_FORMAT(f.arrival_time, '%%H:%%i') AS formatted_arrival_time, 
									f.price,
									DATE(f.departure_time) AS formatted_departure_date,
									a.total_seats,
									(
										SELECT COUNT(*)
										FROM ticket t
										WHERE t.flight_num = f.flight_num
									) AS booked_seats
								FROM 
									flight f
								INNER JOIN 
									airplane a ON f.airplane_id = a.airplane_id
								INNER JOIN
									airline_staff astaff ON f.airline_name = astaff.airline_name
								WHERE 
									UPPER(depart_airport_name) IN %s 
									AND UPPER(arrival_airport_name) IN %s 
									AND DATE(departure_time) = %s 
									AND flight_status = 'upcoming'
									AND astaff.username = %s
								HAVING 
									booked_seats < a.total_seats
								ORDER BY 
									price;
							"""
				flight_cursor.execute(flight_sql, (tuple(source_airports), tuple(destination_airports), search_date, session['username']))
			else:
				flight_sql = """
								SELECT 
									f.airline_name, 
									f.flight_num, 
									TIME_FORMAT(f.departure_time, '%%H:%%i') AS formatted_departure_time, 
									TIME_FORMAT(f.arrival_time, '%%H:%%i') AS formatted_arrival_time, 
									f.price,
									DATE(f.departure_time) AS formatted_departure_date,
									a.total_seats,
									(
										SELECT COUNT(*)
										FROM ticket t
										WHERE t.flight_num = f.flight_num
									) AS booked_seats
								FROM 
									flight f
								INNER JOIN 
									airplane a ON f.airplane_id = a.airplane_id
								WHERE 
									UPPER(depart_airport_name) IN %s 
									AND UPPER(arrival_airport_name) IN %s 
									AND DATE(departure_time) = %s 
									AND flight_status = 'upcoming'
								HAVING 
									booked_seats < a.total_seats
								ORDER BY 
									price;
							"""
				flight_cursor.execute(flight_sql, (tuple(source_airports), tuple(destination_airports), search_date))
			flights = flight_cursor.fetchall()

		print("Flights:", flights)

		if flights:
			return render_template('searchFlights.html', sourcePlaceholder=source_search, destPlaceholder=destination_search, datePlaceholder=search_date, flights_heading='TO '+destination_search, flights=flights)
		else:
			return render_template('searchFlights.html', sourcePlaceholder=source_search, destPlaceholder=destination_search, datePlaceholder=search_date, flights_heading='TO '+destination_search, message="No results found.")
	else:
		return render_template('searchFlights.html', flights_heading='Error', message="Source or destination not found.")

@app.route('/viewFlightsResults', methods=['GET', 'POST'])
def viewFlightsResults():
	source_search = request.form.get('sourceSearch', '').upper()
	destination_search = request.form.get('destinationSearch', '').upper()
	search_from_date = request.form.get('searchFromDate', '')
	search_to_date = request.form.get('searchToDate', '')

	def search_airport(search_term):
		with conn.cursor() as airport_cursor:
			airport_sql = "SELECT airport_name FROM airport WHERE UPPER(airport_city) = %s"
			airport_cursor.execute(airport_sql, search_term)
			results = airport_cursor.fetchall()
			airports = [result[0] if isinstance(result, tuple) else result['airport_name'] for result in results]
			print("Airports in", search_term, ":", airports)
			return airports

	# If source_search is not a city, set source_airports to source_search
	source_airports = search_airport(source_search)
	if not source_airports:
		source_airports = [source_search]

	# If destination_search is not a city, set destination_airports to destination_search
	destination_airports = search_airport(destination_search)
	if not destination_airports:
		destination_airports = [destination_search]


	aCust = False
	aStaff = False
	if source_airports and destination_airports:
		# Execute SQL query to find flights
		with conn.cursor() as flight_cursor:
			if 'booking_agent' in session:
				flight_sql = """
								SELECT 
									f.airline_name, 
									f.flight_num, 
									TIME_FORMAT(f.departure_time, '%%H:%%i') AS formatted_departure_time, 
									TIME_FORMAT(f.arrival_time, '%%H:%%i') AS formatted_arrival_time, 
									f.price,
									DATE(f.departure_time) AS formatted_departure_date,
									c.c_name
								FROM 
									flight f
								INNER JOIN 
									ticket t ON f.flight_num = t.flight_num
								INNER JOIN 
									booking_agent b ON t.booking_agent_id = b.booking_agent_id
								LEFT JOIN 
									customer c ON t.cust_email = c.cust_email
								WHERE 
									UPPER(depart_airport_name) IN %s 
									AND UPPER(arrival_airport_name) IN %s 
									AND DATE(departure_time) BETWEEN %s AND %s
									AND b.booking_agent_email = %s
								ORDER BY 
									formatted_departure_date, formatted_departure_time;
							"""
			elif 'customer' in session:
				flight_sql = """
								SELECT 
									f.airline_name, 
									f.flight_num, 
									TIME_FORMAT(f.departure_time, '%%H:%%i') AS formatted_departure_time, 
									TIME_FORMAT(f.arrival_time, '%%H:%%i') AS formatted_arrival_time, 
									f.price,
									DATE(f.departure_time) AS formatted_departure_date
								FROM 
									flight f
								INNER JOIN 
									ticket t ON f.flight_num = t.flight_num
								WHERE 
									UPPER(depart_airport_name) IN %s 
									AND UPPER(arrival_airport_name) IN %s 
									AND DATE(departure_time) BETWEEN %s AND %s
									AND t.cust_email = %s
								ORDER BY 
									formatted_departure_date, formatted_departure_time;
							"""
				aCust = True
			elif 'airline_staff' in session:
				flight_sql = """
								SELECT 
									f.airline_name, 
									f.flight_num, 
									TIME_FORMAT(f.departure_time, '%%H:%%i') AS formatted_departure_time, 
									TIME_FORMAT(f.arrival_time, '%%H:%%i') AS formatted_arrival_time, 
									f.price,
									DATE(f.departure_time) AS formatted_departure_date
								FROM 
									flight f
								INNER JOIN 
									airplane a ON f.airplane_id = a.airplane_id
								INNER JOIN
									airline_staff astaff ON f.airline_name = astaff.airline_name
								WHERE 
									UPPER(depart_airport_name) IN %s 
									AND UPPER(arrival_airport_name) IN %s 
									AND DATE(departure_time) BETWEEN %s AND %s
									AND astaff.username = %s
								ORDER BY 
									formatted_departure_date, formatted_departure_time;
							"""
				aStaff = True
			flight_cursor.execute(flight_sql, (tuple(source_airports), tuple(destination_airports), search_from_date, search_to_date, session['username']))
			flights = flight_cursor.fetchall()

		print("Flights:", flights)

		if flights:
			return render_template('viewFlights.html', sourcePlaceholder=source_search, destPlaceholder=destination_search, flights_heading='TICKETS TO '+destination_search, flights=flights, aCust=aCust, aStaff=aStaff)
		else:
			return render_template('viewFlights.html', sourcePlaceholder=source_search, destPlaceholder=destination_search, flights_heading='TICKETS TO '+destination_search, message="No results found.")
	else:
		return render_template('viewFlights.html', flights_heading='Error', message="Source or destination not found.")


@app.route('/bookFlight', methods=['POST'])
def bookFlight():
    # Define the generate_ticket_id function
	def generate_ticket_id():
		# Retrieve the last ticket ID based on the booking_date from the database
		cursor = conn.cursor()
		cursor.execute("SELECT ticket_id FROM ticket ORDER BY booking_date DESC LIMIT 1")
		last_ticket_id = cursor.fetchone()

		# If no ticket ID exists, set it to 0
		if last_ticket_id is None:
			last_ticket_id = 0
		else:
			last_ticket_id = int(last_ticket_id[0])

		# Generate a new ticket ID by incrementing the last ticket ID
		new_ticket_id = last_ticket_id + 1

		# Pad the ticket ID with leading zeros to ensure it's 5 digits long
		return str(new_ticket_id).zfill(5)

	# Define the ticket_id_exists function
	def ticket_id_exists(ticket_id):
		# Check if the ticket ID already exists in the database
		cursor = conn.cursor()
		cursor.execute("SELECT COUNT(*) FROM ticket WHERE ticket_id = %s", ticket_id)
		count = cursor.fetchone()[0]
		cursor.close()
		return count > 0

	# Retrieve form data
	flight_number = request.form['flight_number']

	# Generate a unique ticket ID
	ticket_id = generate_ticket_id()

	# Check if the ticket ID already exists and generate a new one if necessary
	while ticket_id_exists(ticket_id):
		ticket_id = generate_ticket_id()

	# Get the current time for booking_date
	booking_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

	if 'username' in session:
		if 'customer' in session:
			cust_email = session['username']
			booking_agent_id = None  # For customers, booking_agent_id is null

			# Insert the ticket into the database
			cursor = conn.cursor()
			cursor.execute("INSERT INTO ticket (ticket_id, flight_num, cust_email, booking_agent_id, booking_date) VALUES (%s, %s, %s, %s, %s)",
							(ticket_id, flight_number, cust_email, booking_agent_id, booking_date))
			conn.commit()
			cursor.close()

			return render_template('successfulBooking.html', ticket_id=ticket_id)
		elif 'booking_agent' in session:
			return render_template('bookFlights.html', flight_number=flight_number, ticket_id=ticket_id)
		else:
			return render_template('login.html', registerSuccess='Log in to book your tickets!')
	else:
		return render_template('login.html', registerSuccess='Log in to book your tickets!')


@app.route('/bookFlights')
def bookFlights():
    # Retrieve ticket_id and flight_number from query parameters
    ticket_id = request.args.get('ticket_id')
    flight_number = request.args.get('flight_number')

    # Pass ticket_id and flight_number to the template
    return render_template('bookFlights.html', ticket_id=ticket_id, flight_number=flight_number)

@app.route('/showCustomer', methods=['GET', 'POST'])
def showCustomer():
    if request.method == 'POST':
        # Retrieve flight_number from the request form
        flight_number = request.form.get('flight_number')

        if flight_number:
            cursor = conn.cursor()
            cursor.execute("SELECT c.c_name FROM customer c INNER JOIN ticket t ON c.cust_email = t.cust_email WHERE t.flight_num = %s;", (flight_number,))
            customers = cursor.fetchall()
            cursor.close()

            if customers:
                return render_template('showCustomer.html', customers=customers, flight_number=flight_number)
            else:
                return render_template('showCustomer.html', message='No customers on flight found.', flight_number=flight_number)
        else:
            return render_template('showCustomer.html', message='Flight number not provided.')
    else:
        # Handle GET request
        return render_template('showCustomer.html', message='')  # Render the form initially

@app.route('/inputCustInfo', methods=['GET', 'POST'])
def inputCustInfo():
	cust_email = request.form['cust_email']
	flight_number = request.form['flight_number']
	ticket_id = request.form['ticket_id']
	booking_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

	cursor = conn.cursor()
	cursor.execute("SELECT booking_agent_id FROM booking_agent WHERE booking_agent_email = %s", session['username'])
	booking_agent_id = cursor.fetchone()[0]
	cursor.close()

	cursor = conn.cursor()
	cursor.execute("INSERT INTO ticket (ticket_id, flight_num, cust_email, booking_agent_id, booking_date) VALUES (%s, %s, %s, %s, %s)",
					(ticket_id, flight_number, cust_email, booking_agent_id, booking_date))
	conn.commit()
	cursor.close()

	return render_template('successfulBooking.html', ticket_id=ticket_id)

@app.route('/awards')
def awards():
	if 'booking_agent' in session:
		cursor = conn.cursor()
		cursor.execute("SELECT booking_agent_id FROM booking_agent WHERE booking_agent_email = %s", session['username'])
		booking_agent_id = cursor.fetchone()[0]
		cursor.close()

		cursor = conn.cursor()
		cursor.execute("""
			SELECT c.c_name, COUNT(t.cust_email) AS num_tickets
			FROM ticket t
			INNER JOIN customer c ON t.cust_email = c.cust_email
			WHERE t.booking_agent_id = %s
			GROUP BY t.cust_email
			ORDER BY num_tickets DESC
			LIMIT 5;
		""", booking_agent_id)
		tcustomer = cursor.fetchall()
		cursor.close()

		cursor = conn.cursor()
		cursor.execute("""
				SELECT c.c_name, SUM(f.price * 0.1) AS commission
				FROM ticket t
				INNER JOIN flight f ON t.flight_num = f.flight_num
				INNER JOIN customer c ON t.cust_email = c.cust_email
				WHERE t.booking_agent_id = %s
				GROUP BY c.c_name
				ORDER BY commission DESC
				LIMIT 5
			""", booking_agent_id)
		ccustomer = cursor.fetchall()
		cursor.close()

		return render_template('awards.html', awards_heading='My Top Customers', tcustomer=tcustomer, ccustomer=ccustomer, award_type='ba', card='card')
	elif 'airline_staff' in session:
		cursor = conn.cursor()
		cursor.execute("SELECT airline_name FROM airline_staff WHERE username = %s", (session['username'],))
		airline_name = cursor.fetchone()[0]
		cursor.close()

		current_date = datetime.now()
		one_month_ago = current_date - timedelta(days=30)
		one_year_ago = current_date - timedelta(days=365)

		# Query to get the top 5 booking agents based on ticket sales for the past month
		query_month = """
							SELECT 
								t.booking_agent_id, 
								COUNT(*) AS ticket_count
							FROM 
								flight f
							INNER JOIN 
								ticket t ON t.flight_num = f.flight_num
							WHERE 
								f.airline_name = %s 
								AND t.booking_date BETWEEN %s AND %s 
								AND t.booking_agent_id IS NOT NULL
							GROUP BY 
								t.booking_agent_id
							ORDER BY 
								ticket_count DESC
							LIMIT 5
		"""

		query_commission = """
							SELECT 
								t.booking_agent_id, 
								SUM(f.price * 0.1) AS commission
							FROM 
								flight f
							INNER JOIN 
								ticket t ON t.flight_num = f.flight_num
							WHERE 
								f.airline_name = %s 
								AND t.booking_date BETWEEN %s AND %s 
								AND t.booking_agent_id IS NOT NULL
							GROUP BY 
								t.booking_agent_id
							ORDER BY 
								commission DESC
							LIMIT 5
		"""

		# Execute the queries for the past month and past year
		cursor = conn.cursor()
		cursor.execute(query_month, (airline_name, one_month_ago,current_date,))
		top_agents_month = cursor.fetchall()

		cursor.execute(query_month, (airline_name, one_year_ago,current_date,))
		top_agents_year = cursor.fetchall()

		cursor.execute(query_commission, (airline_name, one_year_ago,current_date,))
		top_agents_commission = cursor.fetchall()

		cursor.close()

		return render_template('awards.html', awards_heading='Top '+ airline_name +' Booking Agents', top_agents_month=top_agents_month, top_agents_year=top_agents_year, top_agents_commission=top_agents_commission, award_type='st', card='shortcard')
	return render_template('index.html') 

@app.route('/createFlight')
def createFlight():
	if 'admin' in session:
		cursor = conn.cursor()
		query = "SELECT MAX(flight_num) AS max_flight_num FROM flight"
		cursor.execute(query)
		result = cursor.fetchone()

		if result and result[0] is not None:  # Check if result is not empty and the flight number is not None
			max_flight_num = int(result[0])  # Extract the flight number from the result tuple and convert it to an integer
			new_flight_num = max_flight_num + 1
		else:
			new_flight_num = 1

		new_flight_num = str(new_flight_num).zfill(5)
		cursor.close()


		cursor = conn.cursor()
		cursor.execute("SELECT airline_name FROM airline_staff WHERE username = %s", (session['username'],))
		airline_name = cursor.fetchone()[0]
		cursor.close()

		cursor = conn.cursor()
		cursor.execute("SELECT airport_name FROM airport ORDER BY airport_name")
		airport_names = [row[0] for row in cursor.fetchall()]
		cursor.close()

		cursor = conn.cursor()
		cursor.execute("SELECT airplane_id FROM airplane WHERE airline_name =%s", airline_name)
		airplane_id = [row[0] for row in cursor.fetchall()]
		cursor.close()

		return render_template('createFlight.html', flight_num=new_flight_num, airline_name=airline_name, airport_names=airport_names, airplane_id=airplane_id)
	else:
		return render_template('viewFlights.html')
	
@app.route('/inputFlightInfo', methods=['GET', 'POST'])
def inputFlightInfo():
	# flight_num = request.args.get('flight_num')
	# print('showwwwwww',flight_num)
	# airline_name = request.args.get('airline_name')
	# flight_num = request.form['flight_num']
	flight_num = request.form.get('flight_num')
	airline_name = request.form.get('airline_name')
	# airline_name = request.form['airline_name']
	depart_airport_name = request.form['depart_airport_name']
	arrival_airport_name = request.form['arrival_airport_name']
	departure_time = request.form['departure_time']
	arrival_time = request.form['arrival_time']
	price = request.form['price']
	flight_status = 'upcoming'
	airplane_id = request.form['airplane_id']


	cursor = conn.cursor()
	cursor.execute("INSERT INTO flight VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
					(flight_num, airline_name, arrival_airport_name, depart_airport_name, departure_time, arrival_time, price, flight_status, airplane_id))
	conn.commit()
	cursor.close()

	return render_template('viewFlights.html', successfulAdd='Successfully Added Flight!', sourcePlaceholder='From airport/city...', destPlaceholder='To airport/city...')

@app.route('/changeFlightStatus', methods=['GET', 'POST'])
def changeFlightStatus():
	cursor = conn.cursor()
	cursor.execute("SELECT airline_name FROM airline_staff WHERE username = %s", (session['username'],))
	airline_name = cursor.fetchone()[0]
	cursor.close()

	cursor = conn.cursor()
	cursor.execute("SELECT flight_num FROM flight WHERE airline_name =%s ORDER BY flight_num", airline_name)
	flight_num = [row[0] for row in cursor.fetchall()]
	cursor.close()

	return render_template('changeFlightStatus.html', flight_num=flight_num)

@app.route('/changeFlightStatusRequest', methods=['GET', 'POST'])
def changeFlightStatusRequest():
	flight_num = request.form.get('flight_num')
	flight_status = request.form['flight_status']

	cursor = conn.cursor()
	cursor.execute("UPDATE flight SET flight_status = %s WHERE flight_num = %s", (flight_status, flight_num))
	conn.commit()
	cursor.close()

	return render_template('viewFlights.html', successfulAdd='Successfully Updated Flight!', sourcePlaceholder='From airport/city...', destPlaceholder='To airport/city...')

@app.route('/addAirplane', methods=['GET', 'POST'])
def addAirplane():
    cursor = conn.cursor()
    cursor.execute("SELECT airline_name FROM airline_staff WHERE username = %s", (session['username'],))
    airline_name = cursor.fetchone()[0]
    cursor.close()

    cursor = conn.cursor()
    cursor.execute("SELECT MAX(CAST(SUBSTRING(airplane_id, 3) AS UNSIGNED)) AS max_number FROM airplane WHERE airline_name = %s", (airline_name,))
    result = cursor.fetchone()
    cursor.close()

    if result and result[0] is not None:
        max_number = result[0]
        next_number = max_number + 1
    else:
        next_number = 0

    abbreviation = ''.join(word[0] for word in airline_name.split()).upper()
    # Generate the airplane_id with a maximum length of 5 characters
    airplane_id = f"{abbreviation}{next_number:03d}"[:5]

    return render_template('addAirplane.html', airline_name=airline_name, airplane_id=airplane_id)

@app.route('/addAirplaneRequest', methods=['GET', 'POST'])
def addAirplaneRequest():
	airline_name = request.form.get('airline_name')
	airplane_id = request.form.get('airplane_id')[:5]
	total_seats = request.form['total_seats']

	cursor = conn.cursor()
	cursor.execute("INSERT INTO airplane VALUES (%s, %s, %s)",
					(airplane_id, airline_name, total_seats))
	conn.commit()
	cursor.close()

	cursor = conn.cursor()
	cursor.execute("SELECT airplane_id, total_seats FROM airplane WHERE airline_name = %s;", (airline_name,))
	airplanes = cursor.fetchall()
	cursor.close()

	return render_template('showAirplane.html', successfulAdd='Successfully Added Airplane No.'+airplane_id, airline_name=airline_name, airplanes=airplanes)


@app.route('/showAirplane', methods=['GET', 'POST'])
def showAirplane():
	cursor = conn.cursor()
	cursor.execute("SELECT airline_name FROM airline_staff WHERE username = %s", (session['username'],))
	airline_name = cursor.fetchone()[0]
	cursor.close()

	cursor = conn.cursor()
	cursor.execute("SELECT airplane_id, total_seats FROM airplane WHERE airline_name = %s;", (airline_name,))
	airplanes = cursor.fetchall()
	cursor.close()

	if airplanes:
		return render_template('showCustomer.html', airline_name=airline_name, airplanes=airplanes)
	else:
		return render_template('showCustomer.html', message='No customers on flight found.')
	
@app.route('/addAirport')
def addAirport():
	return render_template('addAirport.html')

@app.route('/addAirportRequest', methods=['GET', 'POST'])
def addAirportRequest():
	airport_name = request.form['airport_name']
	airport_city = request.form['airport_city'].upper()

	cursor = conn.cursor()
	cursor.execute("INSERT INTO airport VALUES (%s, %s)",
					(airport_name, airport_city))
	conn.commit()
	cursor.close()

	return render_template('searchFlights.html', successfulAdd='Successfully Added Airport ' + airport_name + ' From ' + airport_city, sourcePlaceholder='From airport/city...', destPlaceholder='To airport/city...')

app.secret_key = 'its a secret shhhhhhh'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)
