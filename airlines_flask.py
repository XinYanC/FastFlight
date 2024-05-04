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
            cursor.execute("SELECT c_name FROM customer WHERE cust_email = %s", (session['username'],))
            c_name = cursor.fetchone()[0]
            cursor.close()

            # Split the full name into words
            name_parts = c_name.split()
            # Join all but the last word
            first_name = ' '.join(name_parts[:-1])
            
            return redirect(url_for('customerInterface', cust_name=first_name))
        elif 'booking_agent' in session:
            cursor = conn.cursor()
            cursor.execute("SELECT booking_agent_id FROM booking_agent WHERE booking_agent_email = %s", (session['username'],))
            booking_agent_id = cursor.fetchone()[0]
            cursor.close()

            return redirect(url_for('bookingAgentInterface', booking_agent_id=booking_agent_id))
        elif 'airline_staff' in session:
            cursor = conn.cursor()
            cursor.execute("SELECT first_name FROM airline_staff WHERE username = %s", (session['username'],))
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
	return render_template('staffInterface.html', staff_name=staff_name)

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
						INNER JOIN
							airline_staff as ON f.airline_name = as.airline_name
						WHERE 
							flight_status = 'upcoming'
						HAVING 
							booked_seats < a.total_seats
						ORDER BY 
							formatted_departure_date, formatted_departure_time;
					"""
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
				cursor.execute(flight_sql)
			else:
				cursor.execute(flight_sql)
			flights = cursor.fetchall()
			return render_template('searchFlights.html', flights_heading='Upcoming Flights', sourcePlaceholder='From airport/city...', destPlaceholder='To airport/city...', datePlaceholder='Select date...', flights=flights, flightDepDate=True)
	finally:
        # Close the database connection
		conn.close()

@app.route('/stats')
def stats():
	# days = request.form['timeRange']
	# if 'booking_agent' in session:

	if 'customer' in session:
		now = datetime.now()
		past_year = now - timedelta(days=365)
		total_amount = 0

		cursor = conn.cursor()
		cursor.execute("""
							SELECT SUM(f.price) AS total_amount, COUNT(*) AS num_flights
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
				SELECT SUM(f.price) AS total_amount
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

		return render_template('stats.html', stats_heading='My Spendings', total_amount=total_amount, now=now, past_year=past_year, monthly_spending=monthly_spending_json, month_labels=month_labels_json)
	return render_template('stats.html')

@app.route('/custStatRange', methods=['GET', 'POST'])
def custStatRange():
	searchFromDate = request.form['searchFromDate']
	searchToDate = request.form['searchToDate']

	if 'customer' in session:
		now = datetime.now()
		past_year = now - timedelta(days=365)
		total_amount = 0

		cursor = conn.cursor()
		cursor.execute("""
							SELECT SUM(f.price) AS total_amount, COUNT(*) AS num_flights
							FROM ticket t
							INNER JOIN flight f ON t.flight_num = f.flight_num
							WHERE t.cust_email = %s
								AND t.booking_date >= %s;
						""", (session['username'], past_year))
		total_amount = cursor.fetchall()[0]  # Fetch the total amount
		cursor.close()

		from_date = datetime.strptime(searchFromDate, "%Y-%m-%d")
		to_date = datetime.strptime(searchToDate, "%Y-%m-%d")

		months_between = [
			from_date + relativedelta(months=i) for i in range((to_date.year - from_date.year) * 12 + to_date.month - from_date.month + 1)
		]
		months_between.reverse()  # Reverse the list to have the oldest month first

		month_labels = [month.strftime("%B %Y") for month in months_between]

		monthly_spending = []

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

		return render_template('stats.html', stats_heading='My Spendings', total_amount=total_amount, now=now, past_year=past_year, monthly_spending=monthly_spending_json, month_labels=month_labels_json)
	return render_template('stats.html')

@app.route('/viewFlights')
def viewFlights():
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

	try:
		# Execute the SQL query
		with conn.cursor() as cursor:
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
	loginError = None

	if(data):
		#creates a session for the the user
		#session is a built in
		session['username'] = username
		if (user == "customer"):
			cursor = conn.cursor()
			cursor.execute("SELECT c_name FROM customer WHERE cust_email = %s", (username))
			c_name = cursor.fetchone()[0]
			cursor.close()

			# Split the full name into words
			name_parts = c_name.split()
			# Join all but the last word
			first_name = ' '.join(name_parts[:-1])
			
			return redirect(url_for('customerInterface', cust_name=first_name))
		elif (user == "booking_agent"):
			cursor = conn.cursor()
			cursor.execute("SELECT booking_agent_id FROM booking_agent WHERE booking_agent_email = %s", (username))
			booking_agent_id = cursor.fetchone()[0]
			cursor.close()

			return redirect(url_for('bookingAgentInterface', booking_agent_id=booking_agent_id))
		elif (user == "airline_staff"):
			cursor = conn.cursor()
			cursor.execute("SELECT first_name FROM airline_staff WHERE username = %s", (username))
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
			airport_cursor.execute(airport_sql, (search_term,))
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
									airline_staff as ON f.airline_name = as.airline_name
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

@app.route('/viewFlightsResults', methods=['POST'])
def viewFlightsResults():
	source_search = request.form['sourceSearch'].upper()  
	destination_search = request.form['destinationSearch'].upper()  
	search_from_date = request.form['searchFromDate']
	search_to_date = request.form['searchToDate']

	def search_airport(search_term):
		with conn.cursor() as airport_cursor:
			airport_sql = "SELECT airport_name FROM airport WHERE UPPER(airport_city) = %s"
			airport_cursor.execute(airport_sql, (search_term,))
			results = airport_cursor.fetchall()
			airports = [result[0] if isinstance(result, tuple) else result['airport_name'] for result in results]
			print("Airports in", search_term, ":", airports)
			return airports

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

	aCust = False
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
			flight_cursor.execute(flight_sql, (tuple(source_airports), tuple(destination_airports), search_from_date, search_to_date, session['username']))
			flights = flight_cursor.fetchall()
			aCust = True

		print("Flights:", flights)

		if flights:
			return render_template('viewFlights.html', sourcePlaceholder=source_search, destPlaceholder=destination_search, flights_heading='TICKETS TO '+destination_search, flights=flights, aCust=aCust)
		else:
			return render_template('viewFlights.html', sourcePlaceholder=source_search, destPlaceholder=destination_search, flights_heading='TICKETS TO '+destination_search, message="No results found.")
	else:
		return render_template('viewFlights.html', flights_heading='Error', message="Source or destination not found.")



@app.route('/bookFlight', methods=['POST'])
def bookFlight():
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

			return render_template('successfulBooking.html')
	else:
		return render_template('login.html', registerSuccess = 'Log in to book your tickets!')
	
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


def ticket_id_exists(ticket_id):
	# Check if the ticket ID already exists in the database
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(*) FROM ticket WHERE ticket_id = %s", (ticket_id,))
	count = cursor.fetchone()[0]
	cursor.close()
	return count > 0
 

app.secret_key = 'its a secret shhhhhhh'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)
