from flask import Flask, render_template, request, redirect, url_for, jsonify
from yahoo_fin.stock_info import *
import cx_Oracle

app = Flask(__name__)

@app.route('/') 
def hello_world():
    return 'Welcome to Virtual Trading Simulator!'

@app.route('/login', methods = ['POST', 'GET'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        dsn = cx_Oracle.makedsn("localhost", 1521, service_name="orcl")
        con = cx_Oracle.connect(user="system", password="oracle", dsn=dsn)
        cursor = con.cursor()

        query = "SELECT * FROM client WHERE client_id=:username AND pass=:password"
        cursor.execute(query, {'username': username, 'password': password})
        result = cursor.fetchone()

        if result:
            return redirect(url_for('dashboard', username=username, message_balanceupdate="",result=""))
        else:
            return render_template('login.html', message='Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods = ['POST', 'GET'])
def user_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        userid = request.form['userid']

        dsn = cx_Oracle.makedsn("localhost", 1521, service_name="orcl")
        con = cx_Oracle.connect(user="system", password="oracle", dsn=dsn)
        cursor = con.cursor()
        try:
            query = "INSERT INTO client VALUES (:userid, :username, 0, :password, :email, 1,0)"
            cursor.execute(query, {'username': username, 'password': password, 'userid': userid, 'email': email})
            con.commit()
        except:
            return render_template('register.html', message='Username already exists')
        return render_template('register.html', message='Registration successful')
    
    return render_template('register.html')

# @app.route('/dashboard/<username>')
# def dashboard(username):
#     dsn = cx_Oracle.makedsn("localhost", 1521, service_name="orcl")
#     con = cx_Oracle.connect(user="system", password="oracle", dsn=dsn)
#     cursor = con.cursor()
#     query = "SELECT balance FROM client WHERE client_id=:username"
#     cursor.execute(query, {'username': username})
#     bal = cursor.fetchone()
#     query="select * from transaction where client_id=:username order by transaction_date desc"
#     cursor.execute(query, {'username': username})
#     transactions = cursor.fetchall()

#     search_results = []
#     if request.method == 'POST':
#         symbol = request.form['stock_input']
#         action = request.form['action']
#         if action == 'search':
#             query = """
#             SELECT s.symbl, s.stock_name, p.quantity
#             FROM stock s
#             LEFT JOIN (
#                 SELECT stock_id, quantity
#                 FROM portfolio
#                 WHERE client_id = :userid
#             ) p ON s.stock_id = p.stock_id
#             WHERE s.symbl = :symbol
#             """
#             cursor.execute(query, {'userid': username, 'symbol': symbol})
#             rows = cursor.fetchall()
#             quote = get_live_price(f'{symbol}.NS')
#             for row in rows:
#                 search_results.append({'symbol': row[0], 'name': row[1], 'quantity': row[2], 'price': quote})

#     return render_template('maininterface.html', username=username, balance = bal[0], transactions = transactions)

@app.route('/dashboard/<username>', methods=['GET', 'POST'])
def dashboard(username):
    dsn = cx_Oracle.makedsn("localhost", 1521, service_name="orcl")
    con = cx_Oracle.connect(user="system", password="oracle", dsn=dsn)
    cursor = con.cursor()
    query = "SELECT balance FROM client WHERE client_id=:username"
    cursor.execute(query, {'username': username})
    bal = cursor.fetchone()
    query="select * from transaction where client_id=:username order by transaction_date desc"
    cursor.execute(query, {'username': username})
    transactions = cursor.fetchall()

    

    


    if request.method == 'POST':
        symbol = request.form['stock_input']
        action = request.form['action']
        search_results = []
        if action == 'search':
            query = """
            SELECT s.symbl, s.stock_name, p.quantity
            FROM stock s
            LEFT JOIN (
                SELECT stock_id, quantity
                FROM portfolio
                WHERE client_id = :userid
            ) p ON s.stock_id = p.stock_id
            WHERE s.symbl = :symbol
            """
            cursor.execute(query, {'userid': username, 'symbol': symbol})
            rows = cursor.fetchall()
            quote = get_live_price(f'{symbol}.NS')
            quote = "{:.2f}".format(quote)
            for row in rows:
                search_results.append({'symbol': row[0], 'name': row[1], 'quantity': row[2], 'price': quote})
            return render_template('maininterface.html', username=username, balance=bal[0], transactions=transactions, search_results=search_results)
        elif action == 'buy':
            stock_symbol = request.form['stock_input']
            quantity = int(request.form['order_quantity'])
            quote = get_live_price(f'{symbol}.NS')
            price = "{:.2f}".format(quote)
            price =int(float(price))    
            total_cost = quantity * price
            
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="orcl")
            con = cx_Oracle.connect(user="system", password="oracle", dsn=dsn)
            cursor = con.cursor()
            
            query = "SELECT balance FROM client WHERE client_id=:username"
            cursor.execute(query, {'username': username})
            balance = int(cursor.fetchone()[0])
            
            if total_cost > balance:
                message = "Insufficient funds to make purchase."
                return render_template('maininterface.html', username=username, balance=bal[0], transactions=transactions, search_results=[], message = message)
            
            # Deduct total cost from balance
            new_balance = balance - total_cost
            query = "UPDATE client SET balance=:new_balance WHERE client_id=:username"
            cursor.execute(query, {'new_balance': new_balance, 'username': username})
            
            # Add new stock purchase to portfolio
            query = "SELECT stock_id FROM stock WHERE symbl=:stock_symbol"
            cursor.execute(query, {'stock_symbol': stock_symbol})
            stock_id = cursor.fetchone()[0]
            
            query = "SELECT quantity FROM portfolio WHERE client_id=:username AND stock_id=:stock_id"
            cursor.execute(query, {'username': username, 'stock_id': stock_id})
            result = cursor.fetchone()
            
            if result:
                # Stock is already in portfolio, update quantity
                new_quantity = result[0] + quantity
                query = "UPDATE portfolio SET quantity=:new_quantity WHERE client_id=:username AND stock_id=:stock_id"
                cursor.execute(query, {'new_quantity': new_quantity, 'username': username, 'stock_id': stock_id})
            else:
                # Stock is not in portfolio, insert new row
                query = "INSERT INTO portfolio (client_id, stock_id, quantity) VALUES (:username, :stock_id, :quantity)"
                cursor.execute(query, {'username': username, 'stock_id': stock_id, 'quantity': quantity})
            
            con.commit()
            con.close()
            
            message = f"{quantity} shares of {stock_symbol} purchased for Rs.{total_cost:.2f}."
            return render_template('maininterface.html', username=username, balance=bal[0], transactions=transactions, search_results=[], message = message)

    
    return render_template('maininterface.html', username=username, balance=bal[0], transactions=transactions, search_results=[])

@app.route('/dashboard/<username>/balance_update', methods=['POST', 'GET'])
def balance_update(username):
    if request.method=='POST':
        amount = int(request.form['balance'])
        action = request.form['action']
        dsn = cx_Oracle.makedsn("localhost", 1521, service_name="orcl")
        con = cx_Oracle.connect(user="system", password="oracle", dsn=dsn)
        cursor = con.cursor()
        if action == 'deposit':
            query = "UPDATE client SET balance = balance + :amount WHERE client_id=:username"
            cursor.execute(query, {'amount': amount, 'username': username})
            con.commit()
            query = "select balance from client where client_id=:username"
            cursor.execute(query, {'username': username})
            balance = int(cursor.fetchone()[0])
            cursor.callproc('update_transaction', [username, 'Deposit', amount])
            con.commit()
            
            return redirect(url_for('dashboard', username=username, message_balanceupdate="Deposit successful", stockid=""))

            # return render_template('maininterface.html', username=username,balance=balance,message_balanceupdate='Deposit successful')
            # Update balance with deposit amount
        elif action == 'withdraw':
            try:
                query = "select balance from client where client_id=:username"
                cursor.execute(query, {'username': username})
                result = cursor.fetchone()
                query = "UPDATE client SET balance = balance - :amount WHERE client_id=:username"
                cursor.execute(query, {'amount': amount, 'username': username})
                con.commit()
                query = "select balance from client where client_id=:username"
                cursor.execute(query, {'username': username})
                balance = int(cursor.fetchone()[0])
                cursor.callproc('update_transaction', [username, 'Withdraw', amount])
                con.commit()
                return redirect (url_for('dashboard', username=username, message_balanceupdate='Withdraw successful', stockid="yrest"))
                # return render_template('maininterface.html', username=username,balance=balance, message_balanceupdate='Withdraw successful')
            except cx_Oracle.DatabaseError as e:
                query = "select balance from client where client_id=:username"
                cursor.execute(query, {'username': username})
                balance = int(cursor.fetchone()[0])
                cursor.callproc('update_transaction', [username, 'Failed', amount])
                con.commit()
                return redirect(url_for('dashboard', username=username,  message_balanceupdate=str(e)))
                # return render_template('maininterface.html', username=username,balance=balance, message_balanceupdate=f'Error {e}')
            # if result[0] < int(amount):
            #     return redirect(url_for('dashboard', username=username,  message_balanceupdate='Insufficient balance'))
            # else:
            #     query = "UPDATE client SET balance = balance - :amount WHERE client_id=:username"
            #     cursor.execute(query, {'amount': amount, 'username': username})
            #     con.commit()
            #     return redirect(url_for('dashboard', username=username,  message_balanceupdate='Withdraw successful'))
            # Update balance with negative of withdraw amount
        return redirect(url_for('dashboard', username=username, message_balanceupdate="", stockid=""))

@app.route('/dashboard/<username>/buy', methods=['POST'])
def buy(username):
    stock_symbol = request.form['stock_symbol']
    quantity = int(request.form['quantity'])
    price = float(request.form['price'])
    total_cost = quantity * price
    
    dsn = cx_Oracle.makedsn("localhost", 1521, service_name="orcl")
    con = cx_Oracle.connect(user="system", password="oracle", dsn=dsn)
    cursor = con.cursor()
    
    query = "SELECT balance FROM client WHERE client_id=:username"
    cursor.execute(query, {'username': username})
    balance = cursor.fetchone()[0]
    
    if total_cost > balance:
        message = "Insufficient funds to make purchase."
        return redirect(url_for('dashboard', username=username, message_balanceupdate=message))
    
    # Deduct total cost from balance
    new_balance = balance - total_cost
    query = "UPDATE client SET balance=:new_balance WHERE client_id=:username"
    cursor.execute(query, {'new_balance': new_balance, 'username': username})
    
    # Add new stock purchase to portfolio
    query = "SELECT stock_id FROM stock WHERE symbol=:stock_symbol"
    cursor.execute(query, {'stock_symbol': stock_symbol})
    stock_id = cursor.fetchone()[0]
    
    query = "SELECT quantity FROM portfolio WHERE client_id=:username AND stock_id=:stock_id"
    cursor.execute(query, {'username': username, 'stock_id': stock_id})
    result = cursor.fetchone()
    
    if result:
        # Stock is already in portfolio, update quantity
        new_quantity = result[0] + quantity
        query = "UPDATE portfolio SET quantity=:new_quantity WHERE client_id=:username AND stock_id=:stock_id"
        cursor.execute(query, {'new_quantity': new_quantity, 'username': username, 'stock_id': stock_id})
    else:
        # Stock is not in portfolio, insert new row
        query = "INSERT INTO portfolio (client_id, stock_id, quantity) VALUES (:username, :stock_id, :quantity)"
        cursor.execute(query, {'username': username, 'stock_id': stock_id, 'quantity': quantity})
    
    con.commit()
    con.close()
    
    message = f"{quantity} shares of {stock_symbol} purchased for ${total_cost:.2f}."
    return redirect(url_for('dashboard', username=username, message_balanceupdate=message))

if __name__ == '__main__':
    app.run(debug=True)