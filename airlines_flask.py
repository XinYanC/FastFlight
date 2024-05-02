# cd FOLDER
# python ./airlines_flask.py

from flask import Flask, render_template, request, url_for, redirect, session, jsonify
import pymysql, pymysql.cursors
import hashlib

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

@app.route('/searchFlights')
def searchFlights():
	flight_sql = """
		SELECT 
			airline_name, 
			flight_num, 
			TIME_FORMAT(departure_time, '%H:%i') AS formatted_departure_time, 
			TIME_FORMAT(arrival_time, '%H:%i') AS formatted_arrival_time,  
			price 
		FROM 
			flight 
		WHERE 
			flight_status = 'upcoming'
		ORDER BY 
			departure_time
	"""

	try:
		# Execute the SQL query
		with conn.cursor() as cursor:
			cursor.execute(flight_sql)
			flights = cursor.fetchall()
			return render_template('searchFlights.html', flights_heading='Upcoming Flights', sourcePlaceholder='From airport/city...', destPlaceholder='To airport/city...', datePlaceholder='Select date...', flights=flights)
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
		query = "SELECT * FROM customer WHERE cust_email = '{}' and c_password = '{}'"
		cursor.execute(query.format(username, hashedPassword))
		data = cursor.fetchone()
	elif (user == "booking_agent"):
		query = "SELECT * FROM booking_agent WHERE booking_agent_email = '{}' and ba_password = '{}'"
		cursor.execute(query.format(username, hashedPassword))
		data = cursor.fetchone()
	elif (user == "airline_staff"):
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
			flight_sql = """
							SELECT 
								airline_name, 
								flight_num, 
								TIME_FORMAT(departure_time, '%%H:%%i') AS formatted_departure_time, 
								TIME_FORMAT(arrival_time, '%%H:%%i') AS formatted_arrival_time, 
								price 
							FROM 
								flight 
							WHERE 
								UPPER(depart_airport_name) IN %s 
								AND UPPER(arrival_airport_name) IN %s 
								AND DATE(departure_time) = %s 
								AND flight_status = 'upcoming'
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




app.secret_key = 'its a secret shhhhhhh'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)
