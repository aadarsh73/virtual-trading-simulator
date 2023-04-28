from flask import Flask, render_template, request, redirect, url_for
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
            return redirect(url_for('dashboard', username=username, message_balanceupdate=""))
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

@app.route('/dashboard/<username>')
def dashboard(username, message_balanceupdate=None):
    dsn = cx_Oracle.makedsn("localhost", 1521, service_name="orcl")
    con = cx_Oracle.connect(user="system", password="oracle", dsn=dsn)
    cursor = con.cursor()
    query = "SELECT balance FROM client WHERE client_id=:username"
    cursor.execute(query, {'username': username})
    bal = cursor.fetchone()
    query="select * from transaction where client_id=:username order by transaction_date desc"
    cursor.execute(query, {'username': username})
    transactions = cursor.fetchall()
    return render_template('maininterface.html', username=username, balance = bal[0], transactions = transactions, message_balanceupdate=message_balanceupdate)
        
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
            
            return redirect(url_for('dashboard', username=username, message_balanceupdate="Deposit successful"))

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
                return redirect (url_for('dashboard', username=username, message_balanceupdate='Withdraw successful'))
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
        return redirect(url_for('dashboard', username=username, message_balanceupdate=""))
if __name__ == '__main__':
    app.run(debug=True)