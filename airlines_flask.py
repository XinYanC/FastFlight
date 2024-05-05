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
	if 'username' in session:
		if 'customer' in session:
			conn.ping(reconnect=True)
			cursor = conn.cursor()
			cursor.execute("SELECT c_name FROM customer WHERE cust_email = %s", session['username'])
			c_name = cursor.fetchone()
			cursor.close()
			if c_name:
				c_name = c_name[0]

				name_parts = c_name.split()
				first_name = ' '.join(name_parts[:-1])

				return redirect(url_for('customerInterface', cust_name=first_name))
			else:
				pass
		elif 'booking_agent' in session:
			conn.ping(reconnect=True)
			cursor = conn.cursor()
			cursor.execute("SELECT booking_agent_id FROM booking_agent WHERE booking_agent_email = '{}'".format(session['username']))
			booking_agent_id = cursor.fetchone()
			cursor.close()
			if booking_agent_id:
				return redirect(url_for('bookingAgentInterface', booking_agent_id=booking_agent_id[0]))
			else:
				pass
		elif 'airline_staff' in session:
			conn.ping(reconnect=True)
			cursor = conn.cursor()
			cursor.execute("SELECT first_name FROM airline_staff WHERE username = %s", session['username'])
			first_name = cursor.fetchone()
			cursor.close()
			if first_name:
				return redirect(url_for('staffInterface', staff_name=first_name[0]))
			else:
				pass
	
	conn.ping(reconnect=True)
	cursor = conn.cursor()
	sql = """
            SELECT a.airport_city, COUNT(*) AS ticket_count
            FROM ticket t
            INNER JOIN flight f ON t.flight_num = f.flight_num
            INNER JOIN airport a ON f.arrival_airport_name = a.airport_name
            GROUP BY a.airport_city
            ORDER BY ticket_count DESC
            LIMIT 10
            """
	cursor.execute(sql)
	top_cities = cursor.fetchall()
	cursor.close()

	cursor = conn.cursor()
	sql = """
            SELECT 
				a.airport_city, 
				f.flight_num, 
				DATE_FORMAT(f.departure_time, '%m/%d/%Y') AS departure_date, 
				(ap.total_seats - COUNT(t.flight_num)) AS seats_left
			FROM 
				flight f
			INNER JOIN 
				airport a ON f.arrival_airport_name = a.airport_name
			LEFT JOIN 
				ticket t ON f.flight_num = t.flight_num
			INNER JOIN 
				airplane ap ON f.airplane_id = ap.airplane_id
			WHERE
				f.flight_status = 'upcoming'
			GROUP BY 
				f.flight_num
			ORDER BY 
				seats_left
			LIMIT 3;
            """
	cursor.execute(sql)
	top_flights = cursor.fetchall()
	cursor.close()

	return render_template('index.html', top_flights=top_flights, top_cities=top_cities)


@app.route('/login')
def login():
	logOutSuccess = request.args.get('logOutSuccess', None)
	if logOutSuccess:
		logOutSuccess = "Logged out successfully!"
		return render_template('login.html', logOutSuccess=logOutSuccess)
	else:
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
	if 'customer' in session:
		cust_name = request.args.get('cust_name', 'again')
		cursor = conn.cursor()
		sql = """
				SELECT a.airport_city, COUNT(*) AS ticket_count
				FROM ticket t
				INNER JOIN flight f ON t.flight_num = f.flight_num
				INNER JOIN airport a ON f.arrival_airport_name = a.airport_name
				GROUP BY a.airport_city
				ORDER BY ticket_count DESC
				LIMIT 10
				"""
		cursor.execute(sql)
		top_cities = cursor.fetchall()
		cursor.close()

		cursor = conn.cursor()
		sql = """
				SELECT 
					a.airport_city, 
					f.flight_num, 
					DATE_FORMAT(f.departure_time, '%m/%d/%Y') AS departure_date, 
					(ap.total_seats - COUNT(t.flight_num)) AS seats_left
				FROM 
					flight f
				INNER JOIN 
					airport a ON f.arrival_airport_name = a.airport_name
				LEFT JOIN 
					ticket t ON f.flight_num = t.flight_num
				INNER JOIN 
					airplane ap ON f.airplane_id = ap.airplane_id
				WHERE
					f.flight_status = 'upcoming'
				GROUP BY 
					f.flight_num
				ORDER BY 
					seats_left
				LIMIT 3;
				"""
		cursor.execute(sql)
		top_flights = cursor.fetchall()
		cursor.close()
		return render_template('customerInterface.html', cust_name=cust_name,top_flights=top_flights, top_cities=top_cities)
	else:
		return render_template('login.html', message='Login in to access page.')

@app.route('/bookingAgentInterface')
def bookingAgentInterface():
	if 'booking_agent' in session:
		booking_agent_id = request.args.get('booking_agent_id', 'again')
		return render_template('bookingAgentInterface.html', booking_agent_id=booking_agent_id)
	return render_template('login.html', message='Login in to access page.')

@app.route('/staffInterface')
def staffInterface():
	if 'airline_staff' in session:
		staff_name = request.args.get('staff_name', 'again') 
		staff_operator = False
		staff_admin = False
		if 'operator' in session:
			staff_operator = True
		if 'admin' in session:
			staff_admin = True

		one_year_ago = datetime.now() - timedelta(days=365)
		three_months_ago = datetime.now() - timedelta(days=3*30)
		today = datetime.now()

		cursor = conn.cursor()
		sql = """
				SELECT a.airport_city, COUNT(*) AS ticket_count
				FROM ticket t
				INNER JOIN flight f ON t.flight_num = f.flight_num
				INNER JOIN airport a ON f.arrival_airport_name = a.airport_name
				WHERE t.booking_date BETWEEN %s AND %s
				GROUP BY a.airport_city
				ORDER BY ticket_count DESC
				LIMIT 3
				"""
		cursor.execute(sql, (three_months_ago, today))
		top_cities_month = cursor.fetchall()
		cursor.execute(sql, (one_year_ago, today))
		top_cities_year = cursor.fetchall()
		cursor.close()

		return render_template('staffInterface.html', staff_name=staff_name, staff_operator=staff_operator, staff_admin=staff_admin, top_cities_month=top_cities_month, top_cities_year=top_cities_year)
	else:
		return render_template('login.html', message='Login in to access page.')

@app.route('/successfulBooking')
def successfulBooking():
	if 'booking_agent' in session:
		return render_template('successfulBooking.html')
	else:
		return render_template('login.html', message='Login in to access page.')

@app.route('/searchFlights')
def searchFlights():
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
		with conn.cursor() as cursor:
			if 'booking_agent' in session:
				cursor.execute(flight_sql, session['username'])
			elif 'airline_staff' in session:
				cursor.execute(flight_sql, session['username'])
			elif 'customer' in session:
				cursor.execute(flight_sql)
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
			formatted_day = day.strftime("%Y-%m-%d")
			cursor.execute("""
				SELECT SUM(f.price * 0.1) AS commission
				FROM ticket t
				INNER JOIN flight f ON t.flight_num = f.flight_num
				WHERE t.booking_agent_id = %s
					AND DATE(t.booking_date) = %s;
			""", (booking_agent_id, formatted_day))
			amount = cursor.fetchone()
			if (amount):
				daily_commission.append(amount[0])
			else:
				daily_commission.append(0)

		cursor.close()

		daily_commission = [float(amount) if amount else 0.0 for amount in daily_commission]
		daily_commission.reverse()

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
		total_amount = cursor.fetchall()[0] 
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

		monthly_spending = [float(amount) if amount else 0.0 for amount in monthly_spending]
		monthly_spending.reverse()

		month_labels_json = json.dumps(month_labels)
		monthly_spending_json = json.dumps(monthly_spending)

		return render_template('stats.html', stats_heading='My Spendings', total_amount=total_amount, now=now, past_year=past_year, monthly_spending=monthly_spending_json, month_labels=month_labels_json, stat_type='cust')
	return render_template('login.html', message='Login in to access page.')

@app.route('/companyStats')
def companyStats():
	if 'airline_staff' in session:
		now = datetime.now()
		last_month_date = now - timedelta(days=30)
		last_year_date = now - timedelta(days=365)

		cursor = conn.cursor()
		cursor.execute("SELECT airline_name FROM airline_staff WHERE username = %s", (session['username'],))
		airline_name = cursor.fetchone()[0]
		cursor.close()

		cursor = conn.cursor()
		cursor.execute("""
			SELECT SUM(f.price) 
			FROM ticket t 
			INNER JOIN flight f ON t.flight_num = f.flight_num 
			WHERE f.airline_name = %s 
				AND t.booking_date >= %s
		""", (airline_name, last_month_date))
		total_month_sales = cursor.fetchone()[0]
		cursor.close()

		cursor = conn.cursor()
		cursor.execute("""
			SELECT SUM(f.price) 
			FROM ticket t 
			INNER JOIN flight f ON t.flight_num = f.flight_num 
			WHERE f.airline_name = %s 
				AND t.booking_date >= %s
		""", (airline_name, last_year_date))
		total_year_sales = cursor.fetchone()[0]
		cursor.close()
		
		def calculate_direct_sales(date):
			cursor = conn.cursor()
			cursor.execute("""
				SELECT SUM(f.price) 
				FROM ticket t 
				INNER JOIN flight f ON t.flight_num = f.flight_num 
				WHERE t.booking_agent_id IS NULL 
					AND f.airline_name = %s 
					AND t.booking_date >= %s
			""", (airline_name, last_month_date))
			direct_sales = cursor.fetchone()[0]
			cursor.close()
			return direct_sales if direct_sales else 0

		def calculate_indirect_sales(date):
			cursor = conn.cursor()
			cursor.execute("""
				SELECT SUM(f.price) 
				FROM ticket t 
				INNER JOIN flight f ON t.flight_num = f.flight_num 
				WHERE t.booking_agent_id IS NOT NULL 
					AND f.airline_name = %s 
					AND t.booking_date >= %s
			""", (airline_name, last_year_date))
			indirect_sales = cursor.fetchone()[0]
			cursor.close()
			return indirect_sales if indirect_sales else 0

		
		direct_sales_last_month = calculate_direct_sales(last_month_date)
		indirect_sales_last_month = calculate_indirect_sales(last_month_date)
		last_month = [total_month_sales, direct_sales_last_month,indirect_sales_last_month]
		direct_sales_last_year = calculate_direct_sales(last_year_date)
		indirect_sales_last_year = calculate_indirect_sales(last_year_date)
		last_year = [total_year_sales, direct_sales_last_year,indirect_sales_last_year]

		past_six_months = [now - timedelta(days=30*i) for i in range(1, 7)]
		month_labels = [month.strftime("%B %Y") for month in past_six_months]
		month_labels.reverse()

		monthly_sold = []

		for month in past_six_months:
			start_of_month = month.replace(day=1)
			end_of_month = month.replace(day=calendar.monthrange(month.year, month.month)[1])

			cursor = conn.cursor()
			cursor.execute("""
				SELECT COUNT(*) AS total_amount
				FROM ticket t 
				INNER JOIN flight f ON t.flight_num = f.flight_num 
				WHERE f.airline_name = %s
					AND DATE(t.booking_date) BETWEEN %s AND %s;
			""", (airline_name, start_of_month.date(), end_of_month.date()))
			amount = cursor.fetchone()[0]
			monthly_sold.append(amount)
			cursor.close()

		month_labels_json = json.dumps(month_labels)
		monthly_earning_json = json.dumps(monthly_sold)
		
		return render_template('companyStats.html', 
								stats_heading='Airline Revenue and Report', 
								last_month=last_month,
								last_year=last_year, 
								now=now,
								past_month=last_month_date,
								last_year_date=last_year_date,
								monthly_earning=monthly_earning_json, 
								month_labels=month_labels_json)
	return render_template('login.html', message='Login in to access page.')

@app.route('/companyStatsResults', methods=['GET', 'POST'])
def companyStatsResults():
	searchFromDate = request.form['searchFromDate']
	searchToDate = request.form['searchToDate']

	if 'airline_staff' in session:
		from_date = datetime.strptime(searchFromDate, "%Y-%m-%d")
		to_date = datetime.strptime(searchToDate, "%Y-%m-%d")


		cursor = conn.cursor()
		cursor.execute("SELECT airline_name FROM airline_staff WHERE username = %s", (session['username'],))
		airline_name = cursor.fetchone()[0]
		cursor.close()

		cursor = conn.cursor()
		cursor.execute("""
			SELECT IFNULL(SUM(f.price), 0)
			FROM ticket t 
			INNER JOIN flight f ON t.flight_num = f.flight_num 
			WHERE f.airline_name = %s 
				AND DATE(t.booking_date) BETWEEN DATE(%s) AND DATE(%s)
		""", (airline_name, from_date, to_date))
		total_month_sales = cursor.fetchone()[0]
		cursor.close()
		
		def calculate_direct_sales(from_date, to_date):
			cursor = conn.cursor()
			cursor.execute("""
				SELECT SUM(f.price) 
				FROM ticket t 
				INNER JOIN flight f ON t.flight_num = f.flight_num 
				WHERE t.booking_agent_id IS NULL 
					AND f.airline_name = %s 
					AND DATE(t.booking_date) BETWEEN DATE(%s) AND DATE(%s)
			""", (airline_name, from_date, to_date))
			direct_sales = cursor.fetchone()[0]
			cursor.close()
			return direct_sales if direct_sales else 0

		def calculate_indirect_sales(from_date, to_date):
			cursor = conn.cursor()
			cursor.execute("""
				SELECT SUM(f.price) 
				FROM ticket t 
				INNER JOIN flight f ON t.flight_num = f.flight_num 
				WHERE t.booking_agent_id IS NOT NULL 
					AND f.airline_name = %s 
					AND DATE(t.booking_date) BETWEEN DATE(%s) AND DATE(%s)
			""", (airline_name, from_date, to_date))
			indirect_sales = cursor.fetchone()[0]
			cursor.close()
			return indirect_sales if indirect_sales else 0

		direct_sales_last_month = calculate_direct_sales(from_date, to_date)
		indirect_sales_last_month = calculate_indirect_sales(from_date, to_date)
		last_month = [total_month_sales, direct_sales_last_month,indirect_sales_last_month]
		
		days_between = (to_date - from_date).days 
		date_range = [to_date - timedelta(days=i) for i in range(days_between)]
		date_range.reverse()

		day_labels = [day.strftime("%m/%d") for day in date_range]

		daily_sold = []

		cursor = conn.cursor()
		for day in date_range:
			cursor.execute("""
				SELECT COUNT(*) AS total_amount
				FROM ticket t
				INNER JOIN flight f ON t.flight_num = f.flight_num
				WHERE f.airline_name = %s
					AND DATE(t.booking_date) = %s;
			""", (airline_name, day))
			amount = cursor.fetchone()
			if (amount):
				daily_sold.append(amount[0])
			else:
				daily_sold.append(0)

		cursor.close()

		daily_sold = [float(amount) if amount else 0.0 for amount in daily_sold]

		day_labels_json = json.dumps(day_labels)
		daily_sold_json = json.dumps(daily_sold)

		
		return render_template('companyStats.html', 
								stats_heading='Airline Revenue and Report', 
								last_month=last_month, 
								now=to_date,
								past_month=from_date,
								monthly_earning=daily_sold_json, 
								month_labels=day_labels_json)
	return render_template('login.html', message='Login in to access page.')

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

		days_between = (to_date - from_date).days + 1
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
			formatted_day = day.strftime("%Y-%m-%d")  
			cursor.execute("""
				SELECT SUM(f.price * 0.1) AS commission
				FROM ticket t
				INNER JOIN flight f ON t.flight_num = f.flight_num
				WHERE t.booking_agent_id = %s
					AND DATE(t.booking_date) = %s;
			""", (booking_agent_id, formatted_day))
			amount = cursor.fetchone()
			if amount:
				daily_commission.append(amount[0])
			else:
				daily_commission.append(0)

		cursor.close()

		# daily_commission.reverse()
		
		daily_commission = [float(amount) if amount else 0.0 for amount in daily_commission]

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

		monthly_spending = [float(amount) if amount else 0.0 for amount in monthly_spending]

		month_labels_json = json.dumps(month_labels)
		monthly_spending_json = json.dumps(monthly_spending)

		return render_template('stats.html', stats_heading='My Spendings', total_amount=total_amount, now=to_date, past_year=from_date, monthly_spending=monthly_spending_json, month_labels=month_labels_json, stat_type='cust')
	return render_template('login.html', message='Login in to access page.')

@app.route('/viewFlights')
def viewFlights():
	if 'username' in session:
		current_date = datetime.now().date()
		end_date = current_date + timedelta(days=30)
		
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
								AND f.departure_time >= DATE(%s)
								AND f.departure_time < DATE(%s)
								AND f.flight_status = 'upcoming'
							ORDER BY 
								formatted_departure_date, formatted_departure_time;
						"""

		try:
			with conn.cursor() as cursor:
				if 'airline_staff' in session: 
					cursor.execute(flight_sql, (session['username'], current_date, end_date))
					print('hello   ',current_date, end_date)
				else:
					cursor.execute(flight_sql, session['username'])
				flights = cursor.fetchall()
				if (flights):
					return render_template('viewFlights.html', flights_heading='View Upcoming Flights', sourcePlaceholder='From airport/city...', destPlaceholder='To airport/city...', datePlaceholder='Select date...', flights=flights, flightDepDate=True)
				else:
					return render_template('viewFlights.html', flights_heading='No Upcoming Flights', sourcePlaceholder='From airport/city...', destPlaceholder='To airport/city...', datePlaceholder='Select date...')
		finally:
			conn.close()
	else:
		return render_template('login.html', message='Login in to access page.')


#Authenticates the login
@app.route('/loginSubmit', methods=['GET', 'POST'])
def loginSubmit():
	#grabs information from the forms
	username = request.form['login_email']
	password = request.form['login_password']
	user = request.form.get('user_type')

	hashedPassword = hashlib.md5(password.encode()).hexdigest()

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
	cursor.close()

	cursor = conn.cursor()
	if 'airline_staff' in session:
		query = "SELECT permission FROM permission WHERE username = %s"
		cursor.execute(query, (username,))
		staff_status = cursor.fetchall()
		for status in staff_status:
			if status[0] == 'admin':  
				session['admin'] = True
				print('Admin:', session['admin'])
			if status[0] == 'operator': 
				session['operator'] = True
				print('Operator:', session['operator'])
	cursor.close()

	loginError = None

	if(data):
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
		loginError = 'Invalid login or username'
		return render_template('login.html', loginError=loginError)
	

#Authenticates the register
@app.route('/customerRegister', methods=['GET', 'POST'])
def customerRegister():
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

	cursor = conn.cursor()
	query = "SELECT * FROM customer WHERE cust_email = '{}'"
	cursor.execute(query.format(cust_email))
	data = cursor.fetchone()
	registrationError = None
	if(data):
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
	bagent_email = request.form['bagent_email']
	bagent_password = request.form['bagent_password']
	bagent_id = request.form['bagent_id']

	hashedPassword = hashlib.md5(bagent_password.encode()).hexdigest()

	cursor = conn.cursor()
	query = "SELECT * FROM booking_agent WHERE booking_agent_email = '{}'"
	cursor.execute(query.format(bagent_email))
	data = cursor.fetchone()
	registrationError = None

	if(data):
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
	staff_user = request.form['staff_user']
	staff_password = request.form['staff_password']
	staff_fname = request.form['staff_fname']
	staff_lname = request.form['staff_lname']
	staff_dob = request.form['staff_dob']
	staff_airline = request.form.get('staff_airline')

	hashedPassword = hashlib.md5(staff_password.encode()).hexdigest()

	cursor = conn.cursor()
	query = "SELECT * FROM airline_staff WHERE username = '{}'"
	cursor.execute(query.format(staff_user))
	data = cursor.fetchone()
	registrationError = None

	if(data):
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
    return redirect('/login?logOutSuccess=Logged out successfully!')

@app.route('/get_airport_suggestions', methods=['POST'])
def get_airport_suggestions(): 
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

	def search_airport(search_term):
		with conn.cursor() as airport_cursor:
			airport_sql = "SELECT airport_name FROM airport WHERE UPPER(airport_city) = %s"
			airport_cursor.execute(airport_sql, search_term)
			results = airport_cursor.fetchall()
			airports = [result[0] if isinstance(result, tuple) else result['airport_name'] for result in results]
			print("Airports in", search_term, ":", airports)
			return airports

	if not search_airport(source_search):
		source_airports = [source_search]
	else:
		source_airports = search_airport(source_search)

	if not search_airport(destination_search):
		destination_airports = [destination_search]
	else:
		destination_airports = search_airport(destination_search)

	if source_airports and destination_airports:
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

		if flights:
			return render_template('searchFlights.html', sourcePlaceholder=source_search, destPlaceholder=destination_search, datePlaceholder=search_date, flights_heading='TO '+destination_search, flights=flights)
		else:
			return render_template('searchFlights.html', sourcePlaceholder=source_search, destPlaceholder=destination_search, datePlaceholder=search_date, flights_heading='TO '+destination_search, message="No results found.")
	else:
		return render_template('searchFlights.html', flights_heading='Error', message="Source or destination not found.")

@app.route('/viewFlightsResults', methods=['GET', 'POST'])
def viewFlightsResults():
	if 'username' in session:
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
	else:
		return render_template('login.html', message='Login in to access page.')

@app.route('/bookFlight', methods=['POST'])
def bookFlight():

	flight_number = request.form['flight_number']

	conn.ping(reconnect=True)
	cursor = conn.cursor()
	cursor.execute("SELECT MAX(ticket_id) FROM ticket ORDER BY ticket_id")
	last_ticket_id = cursor.fetchone()

	if last_ticket_id is None:
		last_ticket_id = 0
	else:
		last_ticket_id = int(last_ticket_id[0])

	new_ticket_id = last_ticket_id + 1
	ticket_id = str(new_ticket_id).zfill(5)

	# while ticket_id_exists(ticket_id):
	# 	cursor.execute("SELECT ticket_id FROM ticket ORDER BY booking_date DESC LIMIT 1")
		
	# 	last_ticket_id = cursor.fetchone()

	# 	if last_ticket_id is None:
	# 		last_ticket_id = 0
	# 	else:
	# 		last_ticket_id = int(last_ticket_id[0])

	# 	new_ticket_id = last_ticket_id + 1
	# 	ticket_id = str(new_ticket_id).zfill(5)
	cursor.close()

	booking_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

	if 'username' in session:
		if 'customer' in session:
			cust_email = session['username']
			booking_agent_id = None  

			cursor = conn.cursor()
			cursor.execute("INSERT INTO ticket (ticket_id, flight_num, cust_email, booking_agent_id, booking_date) VALUES (%s, %s, %s, %s, %s)",
							(ticket_id, flight_number, cust_email, booking_agent_id, booking_date))
			conn.commit()
			cursor.close()

			return render_template('successfulBooking.html', ticket_id=ticket_id)
		elif 'booking_agent' in session:
			return render_template('bookFlights.html', flight_number=flight_number, ticket_id=ticket_id)
		elif 'airline_staff' in session:
			return render_template('login.html', message='Log in to book your tickets!')
		else:
			return render_template('login.html', message='Log in to book your tickets!')
	else:
		return render_template('login.html', message='Log in to book your tickets!')

# def ticket_id_exists(ticket_id):
# 		cursor = conn.cursor()
# 		cursor.execute("SELECT COUNT(*) FROM ticket WHERE ticket_id = %s", ticket_id)
# 		count = cursor.fetchone()[0]
# 		cursor.close()
# 		return count > 0

@app.route('/bookFlights')
def bookFlights():
	if 'booking_agent' in session:
		ticket_id = request.args.get('ticket_id')
		flight_number = request.args.get('flight_number')

		return render_template('bookFlights.html', ticket_id=ticket_id, flight_number=flight_number)
	else:
		return render_template('login.html', message='Login in to access page.')

@app.route('/showCustomer', methods=['GET', 'POST'])
def showCustomer():
	if 'airline_staff' in session:
		if request.method == 'POST':
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
			return render_template('showCustomer.html', message='*Flight number not provided.') 
	else:
		return render_template('login.html', message='Login in to access page.')

@app.route('/inputCustInfo', methods=['GET', 'POST'])
def inputCustInfo():
	if 'booking_agent' in session:
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
	else:
		return render_template('login.html', message='Login in to access page.')

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
	else:
		return render_template('login.html', message='Login in to access page.')

@app.route('/createFlight')
def createFlight():
	if 'admin' in session:
		cursor = conn.cursor()
		query = "SELECT MAX(flight_num) AS max_flight_num FROM flight"
		cursor.execute(query)
		result = cursor.fetchone()

		if result and result[0] is not None:  
			max_flight_num = int(result[0])  
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
		return render_template('viewFlights.html', flights_heading='No Upcoming Flights')
	
@app.route('/inputFlightInfo', methods=['GET', 'POST'])
def inputFlightInfo():
	if 'admin' in session:
		flight_num = request.form.get('flight_num')
		airline_name = request.form.get('airline_name')
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
	else:
		return render_template('login.html', message='Login in to access page.')

@app.route('/changeFlightStatus', methods=['GET', 'POST'])
def changeFlightStatus():
	if 'operator' in session:
		cursor = conn.cursor()
		cursor.execute("SELECT airline_name FROM airline_staff WHERE username = %s", (session['username'],))
		airline_name = cursor.fetchone()[0]
		cursor.close()

		cursor = conn.cursor()
		cursor.execute("SELECT flight_num FROM flight WHERE airline_name =%s ORDER BY flight_num", airline_name)
		flight_num = [row[0] for row in cursor.fetchall()]
		cursor.close()

		return render_template('changeFlightStatus.html', flight_num=flight_num)
	else:
		return render_template('login.html', message='Login in to access page.')

@app.route('/changeFlightStatusRequest', methods=['GET', 'POST'])
def changeFlightStatusRequest():
	if 'operator' in session:
		flight_num = request.form.get('flight_num')
		flight_status = request.form['flight_status']

		cursor = conn.cursor()
		cursor.execute("UPDATE flight SET flight_status = %s WHERE flight_num = %s", (flight_status, flight_num))
		conn.commit()
		cursor.close()

		return render_template('viewFlights.html', successfulAdd='Successfully Updated Flight!', sourcePlaceholder='From airport/city...', destPlaceholder='To airport/city...')
	else:
		return render_template('login.html', message='Login in to access page.')

@app.route('/addAirplane', methods=['GET', 'POST'])
def addAirplane():
	if 'admin' in session:
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
	else:
		return render_template('login.html', message='Login in to access page.')

@app.route('/addAirplaneRequest', methods=['GET', 'POST'])
def addAirplaneRequest():
	if 'admin' in session:
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
	else:
		return render_template('login.html', message='Login in to access page.')

@app.route('/showAirplane', methods=['GET', 'POST'])
def showAirplane():
	if 'admin' in session:
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
	else:
		return render_template('login.html', message='Login in to access page.')

@app.route('/addAirport')
def addAirport():
	if 'admin' in session:
		return render_template('addAirport.html')
	else:
		return render_template('login.html', message='Login in to access page.')

@app.route('/addAirportRequest', methods=['GET', 'POST'])
def addAirportRequest():
	if 'admin' in session:
		airport_name = request.form['airport_name']
		airport_city = request.form['airport_city'].upper()

		cursor = conn.cursor()
		cursor.execute("INSERT INTO airport VALUES (%s, %s)",
						(airport_name, airport_city))
		conn.commit()
		cursor.close()

		return render_template('searchFlights.html', successfulAdd='Successfully Added Airport ' + airport_name + ' From ' + airport_city, sourcePlaceholder='From airport/city...', destPlaceholder='To airport/city...')
	else:
		return render_template('login.html', message='Login in to access page.')

@app.route('/addPermission', methods=['GET', 'POST'])
def addPermission():
	if 'admin' in session:
		return render_template('addPermission.html')
	else:
		return render_template('login.html', message='Login in to access page.')

@app.route('/addPermissionRequest', methods=['GET', 'POST'])
def addPermissionRequest():
	if 'admin' in session:
		username = request.form['username']
		permission = request.form['permission']

		cursor = conn.cursor()
		cursor.execute("SELECT airline_name FROM airline_staff WHERE username = %s", (session['username'],))
		airline_name = cursor.fetchone()[0]
		cursor.close()

		cursor = conn.cursor()
		sql = "SELECT 1 FROM airline_staff WHERE username = %s AND airline_name = %s LIMIT 1"
		cursor.execute(sql, (username, airline_name))
		result = cursor.fetchone()
		
		if result:
			cursor.execute("INSERT INTO permission VALUES (%s, %s)",
							(username, permission))
			conn.commit()
			cursor.close()
			return render_template('searchFlights.html', successfulAdd='Successfully Granted ' + username + ' ' + permission + ' Permission', sourcePlaceholder='From airport/city...', destPlaceholder='To airport/city...')
		else:
			cursor.close()
			return render_template('addPermission.html', successfulAdd='*Permission Failed - Staff ' + username + ' does not work for ' + airline_name)
	else:
		return render_template('login.html', message='Login in to access page.')

@app.route('/addBookingAgent', methods=['GET', 'POST'])
def addBookingAgent():
	if 'admin' in session:
		conn.ping(reconnect=True)
		cursor = conn.cursor()
		cursor.execute("SELECT airline_name FROM airline_staff WHERE username = %s", (session['username'],))
		airline_name = cursor.fetchone()[0]
		cursor.close()
		return render_template('addBookingAgent.html', airline_name=airline_name)
	else:
		return render_template('login.html', message='Login in to access page.')

@app.route('/addBookingAgentRequest', methods=['GET', 'POST'])
def addBookingAgentRequest():
	if 'admin' in session:
		airline_name = request.form.get('airline_name')
		booking_agent_email = request.form['booking_agent_email']

		cursor = conn.cursor()
		sql = "SELECT 1 FROM booking_agent WHERE booking_agent_email = %s LIMIT 1"
		cursor.execute(sql, (booking_agent_email))
		result = cursor.fetchone()

		if result:
			cursor.execute("INSERT INTO works_for VALUES (%s, %s)",
							(airline_name, booking_agent_email))
			conn.commit()
			cursor.close()
			return render_template('searchFlights.html', successfulAdd='Successfully Added ' + booking_agent_email + ' To ' + airline_name, sourcePlaceholder='From airport/city...', destPlaceholder='To airport/city...')
		else:
			cursor.close()
			return render_template('addBookingAgent.html', successfulAdd=booking_agent_email + ' is not registered', airline_name=airline_name)
	else:
		return render_template('login.html', message='Login in to access page.')

@app.route('/searchCustomer', methods=['GET', 'POST'])
def searchCustomer():
	if 'airline_staff' in session:
		cursor = conn.cursor()
		cursor.execute("SELECT airline_name FROM airline_staff WHERE username = %s", (session['username'],))
		airline_name = cursor.fetchone()[0]
		cursor.close()

		cursor = conn.cursor()
		sql = """
				SELECT c.c_name, COUNT(t.ticket_id) AS ticket_count, c.cust_email
				FROM ticket t
				INNER JOIN customer c ON t.cust_email = c.cust_email
				INNER JOIN flight f ON t.flight_num = f.flight_num
				WHERE f.airline_name = %s
				GROUP BY c.c_name
				ORDER BY ticket_count DESC
				LIMIT %s
			"""
		cursor.execute(sql, (airline_name, 10))
		customers = cursor.fetchall()
		cursor.close()

		return render_template('searchCustomer.html', cust_email='Enter customer email...', custNum='XXXX', cust_heading='Most Frequent Customers', customers=customers, result=False, airline_name=airline_name)
	else:
		return render_template('login.html', message='Login in to access page.')

@app.route('/searchCustomerResult', methods=['GET', 'POST'])
def searchCustomerResult():
	if 'airline_staff' in session:
		airline_name = request.args.get('airline_name')
		cust_email_unhide = request.form.get('cust_email')
		cust_email_hide = request.args.get('cust_email_hide')
		custNum = request.form.get('custNum')
		if cust_email_unhide:
			cust_email = cust_email_unhide
		else:
			cust_email = cust_email_hide

		cursor = conn.cursor()
		sql = "SELECT c_name FROM customer WHERE cust_email = %s"
		cursor.execute(sql, (cust_email,))
		c_name = cursor.fetchone()[0]
		cursor.close()

		if custNum:
			cursor = conn.cursor()
			cursor.execute("SELECT RIGHT(phone_number, 4) FROM customer WHERE cust_email = %s", (cust_email,))
			result = cursor.fetchone()[0]
			cursor.close()

			if result == custNum:
				cursor = conn.cursor()
				sql = """
					SELECT 
						f.airline_name, 
						f.flight_num, 
						TIME_FORMAT(f.departure_time, '%%H:%%i') AS formatted_departure_time, 
						TIME_FORMAT(f.arrival_time, '%%H:%%i') AS formatted_arrival_time, 
						f.price,
						DATE(f.departure_time) AS formatted_departure_date,
						a.airport_name,
						a.airport_city
					FROM 
						ticket t
					INNER JOIN 
						customer c ON t.cust_email = c.cust_email
					INNER JOIN 
						flight f ON t.flight_num = f.flight_num
					INNER JOIN 
						airport a ON f.depart_airport_name = a.airport_name
					WHERE 
						f.airline_name = %s
						AND c.cust_email = %s;
				"""
				cursor.execute(sql, (airline_name, cust_email))
				customerData = cursor.fetchall()
				cursor.close()

				return render_template('searchCustomer.html', cust_email=cust_email, custNum=custNum, cust_heading='Most Frequent Customers', result=True, customerData=customerData)
			else:
					return render_template('searchCustomer.html', cust_heading='User Not Found', result=True, message='Customer information does not match. Please try again.', cust_email='Enter customer email...', custNum='XXXX')
		else:
			cursor = conn.cursor()
			sql = """
				SELECT 
					f.airline_name, 
					f.flight_num, 
					TIME_FORMAT(f.departure_time, '%%H:%%i') AS formatted_departure_time, 
					TIME_FORMAT(f.arrival_time, '%%H:%%i') AS formatted_arrival_time, 
					f.price,
					DATE(f.departure_time) AS formatted_departure_date,
					a.airport_name,
					a.airport_city
				FROM 
					ticket t
				INNER JOIN 
					customer c ON t.cust_email = c.cust_email
				INNER JOIN 
					flight f ON t.flight_num = f.flight_num
				INNER JOIN 
					airport a ON f.depart_airport_name = a.airport_name
				WHERE 
					f.airline_name = %s
					AND c.cust_email = %s;
			"""
			cursor.execute(sql, (airline_name, cust_email))
			customerData = cursor.fetchall()
			cursor.close()

			print(customerData[0])

			return render_template('searchCustomer.html', cust_email=cust_email, custNum='XXXX', cust_heading=c_name+'\'s History', result=True, customerData=customerData)
	else:
		return render_template('login.html', message='Login in to access page.')
	
app.secret_key = 'its a secret shhhhhhh'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)
