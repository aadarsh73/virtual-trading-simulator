from flask import Flask, render_template, request, redirect, url_for
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
        query = "select active from client where client_id=:username"
        cursor.execute(query, {'username': username})
        result = cursor.fetchone()
        if result[0] == 0:
            return render_template('login.html', message='User blocked, contact admin')
        
        query = "SELECT * FROM client WHERE client_id=:username AND pass=:password"
        cursor.execute(query, {'username': username, 'password': password})
        result = cursor.fetchone()
        print(result)
        if result[5] == 1:
            return redirect(url_for('admin', username=username))

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
            query = "INSERT INTO client VALUES (:userid, :username, 0, :password, :email, 0,1)"
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

    # query = """
    #     SELECT s.stock_name, A
    #     """

    # query = """
    #     SELECT s.stock_name, p.quantity, s.symbl
    #     FROM stock s
    #     LEFT JOIN (
    #         SELECT stock_id, quantity
    #         FROM portfolio
    #         WHERE client_id = :userid
    #     ) p ON s.stock_id = p.stock_id
    #     WHERE p.quantity > 0
    # """
    # cursor.execute(query, {'userid': username})
    # rows = cursor.fetchall()
    # portfolio = []
    # for row in rows:
    #     quote = get_live_price(f'{row[2]}.NS')
    #     quote = "{:.2f}".format(quote)
    #     portfolio.append({'name': row[0], 'quantity': row[1], 'price': quote})

    # portfolio = cursor.execute(
    #     'SELECT stock_id, quantity FROM portfolio WHERE client_id = ?', (username)
    # ).fetchall()
    # query = """
    #     SELECT s.stock_id, s.stock_name, s.symbl, p.quantity, p.stock_value, COALESCE(buy_orders.avg_price, 0) as buy_price
    #     FROM stock s
    #     INNER JOIN portfolio p ON s.stock_id = p.stock_id
    #     LEFT JOIN (
    #         SELECT stock_id, AVG(price) as avg_price
    #         FROM (
    #             SELECT stock_id, price
    #             FROM orders
    #             WHERE client_id = :username AND order_type = 'buy'
    #             ORDER BY date_time DESC
    #             FETCH NEXT 5 ROWS ONLY
    #         )
    #         GROUP BY stock_id
    #     ) buy_orders ON s.stock_id = buy_orders.stock_id
    #     WHERE p.client_id = :username
    #     """
    # portfolio_query = '''
    #     SELECT s.stock_id, s.stock_name, s.symbl, p.quantity, AVG(o.price) as buy_price
    #     FROM stock s
    #     INNER JOIN portfolio p ON s.stock_id = p.stock_id
    #     LEFT JOIN (
    #         SELECT stock_id, price
    #         FROM (
    #             SELECT stock_id, price
    #             FROM orders
    #             WHERE client_id = :username AND order_type = 'BUY'
    #             ORDER BY date_time DESC
    #         )
    #         WHERE ROWNUM <= 50
    #     ) o ON s.stock_id = o.stock_id
    #     WHERE p.client_id = :username
    #     GROUP BY s.stock_id, s.stock_name, s.symbl, p.quantity, o.price
    #     ORDER BY s.symbl
    #     '''
    
    portfolio_query = '''
        SELECT s.stock_id, s.stock_name, s.symbl, p.quantity, AVG(o.price) as buy_price
        FROM stock s
        INNER JOIN portfolio p ON s.stock_id = p.stock_id
        LEFT JOIN (
            SELECT stock_id, price
            FROM (
                SELECT stock_id, price
                FROM orders
                WHERE client_id = :username AND order_type = 'BUY'
                ORDER BY date_time DESC
            )
            WHERE ROWNUM <= 50
        ) o ON s.stock_id = o.stock_id
        WHERE p.client_id = :username
        GROUP BY s.stock_id, s.stock_name, s.symbl, p.quantity
        ORDER BY s.symbl
    '''
    portfolio = cursor.execute(portfolio_query, {'username': username}).fetchall()
    alterable_portfolio = []
    profit = 0
    invested = 0
    curr_val = 0

    watchlist_query = '''
                select symbl, stock_name from stock natural join watchlist where client_id=:username
            '''
    watchlist = cursor.execute(watchlist_query, {'username': username}).fetchall()
    watchlist_new = watchlist
    watchlist = []
    for x in watchlist_new:
        watchlist.append(list(x))
    for i in watchlist :
        quote = get_live_price(f'{i[0]}.NS')
        i.append("{:.2f}".format(quote))
    # print(watchlist)
    for x in portfolio:
        alterable_portfolio.append(list(x))
    # print(alterable_portfolio)
    for x in alterable_portfolio:
        if x[4] == None:
            break;
        quote = get_live_price(f'{x[2]}.NS')
        print("Quote is " + str(quote))
        x[4] = "{:.2f}".format(float(x[4]))
        x.append("{:.2f}".format(quote))
        x.append("{:.2f}".format(x[3]*quote))
        x.append("{:.2f}".format(x[3]*float(x[4])))
        x.append("{:.2f}".format(float(x[6])-float(x[7])))
        profit += float(x[8])
        invested += float(x[7])
        curr_val += float(x[6])
    
    alterable_portfolio.append("{:.2f}".format(profit))
    alterable_portfolio.append(invested)
    alterable_portfolio.append(curr_val)
    alterable_portfolio.append(len(alterable_portfolio)+1)
    # print(alterable_portfolio)
    portfolio = alterable_portfolio

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
            portfolio = cursor.execute(portfolio_query, {'username': username}).fetchall()
            alterable_portfolio = []
            profit = 0
            invested = 0
            curr_val = 0
            
            for x in portfolio:
                alterable_portfolio.append(list(x))
            print(alterable_portfolio)
            for x in alterable_portfolio:
                if x[4] == None:
                    break;
                quote = get_live_price(f'{x[2]}.NS')
                print("Quote is " + str(quote))
                x[4] = "{:.2f}".format(float(x[4]))
                x.append("{:.2f}".format(quote))
                x.append("{:.2f}".format(x[3]*quote))
                x.append("{:.2f}".format(x[3]*float(x[4])))
                x.append("{:.2f}".format(float(x[6])-float(x[7])))
                profit += float(x[8])
                invested += float(x[7])
                curr_val += float(x[6])
            
            alterable_portfolio.append("{:.2f}".format(profit))
            alterable_portfolio.append(invested)
            alterable_portfolio.append(curr_val)
            alterable_portfolio.append(len(alterable_portfolio)+1)
            # print(alterable_portfolio)
            portfolio = alterable_portfolio
            watchlist = cursor.execute(watchlist_query, {'username': username}).fetchall()
            watchlist_new = watchlist
            watchlist = []
            for x in watchlist_new:
                watchlist.append(list(x))
            for i in watchlist :
                quote = get_live_price(f'{i[0]}.NS')
                i.append("{:.2f}".format(quote))
            return render_template('maininterface.html', username=username, balance=bal[0], transactions=transactions, search_results=search_results, portfolio=portfolio, watchlist=watchlist, symbol = symbol)
        elif action == 'buy':
            stock_symbol = request.form['stock_input']
            quantity = int(request.form['order_quantity'])
            quote = get_live_price(f'{symbol}.NS')
            price = "{:.2f}".format(quote)
            price =float(price)
            total_cost = quantity * price
            
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="orcl")
            con = cx_Oracle.connect(user="system", password="oracle", dsn=dsn)
            cursor = con.cursor()
            
            query = "SELECT balance FROM client WHERE client_id=:username"
            cursor.execute(query, {'username': username})
            balance = float(cursor.fetchone()[0])
            
            if total_cost > balance:
                message = "Insufficient funds to make purchase."
                watchlist = cursor.execute(watchlist_query, {'username': username}).fetchall()
                watchlist_new = watchlist
                watchlist = []
                for x in watchlist_new:
                    watchlist.append(list(x))
                for i in watchlist :
                    quote = get_live_price(f'{i[0]}.NS')
                    i.append("{:.2f}".format(quote))
                return render_template('maininterface.html', username=username, balance=bal[0], transactions=transactions, search_results=[], message = message, portfolio=portfolio, watchlist=watchlist)
            
            # Deduct total cost from balance

            cursor.callproc('buy_stock', [username, stock_symbol, quantity, price])
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
            
            query = "SELECT balance FROM client WHERE client_id=:username"
            cursor.execute(query, {'username': username})
            bal = cursor.fetchone()
            query="select * from transaction where client_id=:username order by transaction_date desc"
            cursor.execute(query, {'username': username})
            transactions = cursor.fetchall()
            portfolio = cursor.execute(portfolio_query, {'username': username}).fetchall()
            alterable_portfolio = []
            profit = 0
            invested = 0
            curr_val = 0
            
            for x in portfolio:
                alterable_portfolio.append(list(x))
            print(alterable_portfolio)
            for x in alterable_portfolio:
                if x[4] == None:
                    break;
                quote = get_live_price(f'{x[2]}.NS')
                print("Quote is " + str(quote))
                x[4] = "{:.2f}".format(float(x[4]))
                x.append("{:.2f}".format(quote))
                x.append("{:.2f}".format(x[3]*quote))
                x.append("{:.2f}".format(x[3]*float(x[4])))
                x.append("{:.2f}".format(float(x[6])-float(x[7])))
                profit += float(x[8])
                invested += float(x[7])
                curr_val += float(x[6])
            
            alterable_portfolio.append("{:.2f}".format(profit))
            alterable_portfolio.append(invested)
            alterable_portfolio.append(curr_val)
            alterable_portfolio.append(len(alterable_portfolio)+1)
            # print(alterable_portfolio)
            portfolio = alterable_portfolio
            watchlist = cursor.execute(watchlist_query, {'username': username}).fetchall()
            watchlist_new = watchlist
            watchlist = []
            for x in watchlist_new:
                watchlist.append(list(x))
            for i in watchlist :
                quote = get_live_price(f'{i[0]}.NS')
                i.append("{:.2f}".format(quote))
            con.commit()
            con.close()
            action=''
            message = f"{quantity} shares of {stock_symbol} purchased for Rs.{total_cost:.2f}."
            return render_template('maininterface.html', username=username, balance=bal[0], transactions=transactions, search_results=[], message = message, portfolio=portfolio, watchlist=watchlist)
        elif action == 'sell':
            stock_symbol = request.form['stock_input']
            quantity = int(request.form['order_quantity'])
            quote = get_live_price(f'{symbol}.NS')
            price = "{:.2f}".format(quote)
            price =float(price)    
            total_cost = quantity * price
            
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="orcl")
            con = cx_Oracle.connect(user="system", password="oracle", dsn=dsn)
            cursor = con.cursor()
            
            query = "SELECT balance FROM client WHERE client_id=:username"
            cursor.execute(query, {'username': username})
            balance = int(cursor.fetchone()[0])
            query = "SELECT quantity FROM portfolio WHERE stock_id = (select stock_id from stock where symbl=:stock_symbol) and client_id=:username"
            cursor.execute(query, {'stock_symbol': stock_symbol, 'username': username})
            quantity_available = cursor.fetchone()

            if quantity_available is None:
                message = "You dont own this stock."
                watchlist = cursor.execute(watchlist_query, {'username': username}).fetchall()
                watchlist_new = watchlist
                watchlist = []
                for x in watchlist_new:
                    watchlist.append(list(x))
                for i in watchlist :
                    quote = get_live_price(f'{i[0]}.NS')
                    i.append("{:.2f}".format(quote))
                return render_template('maininterface.html', username=username, balance=bal[0], transactions=transactions, search_results=[], message = message, portfolio=portfolio, watchlist=watchlist)
            elif int(quantity_available[0])<quantity:
                message = "Not enough shares to sell."
                watchlist = cursor.execute(watchlist_query, {'username': username}).fetchall()
                watchlist_new = watchlist
                watchlist = []
                for x in watchlist_new:
                    watchlist.append(list(x))
                for i in watchlist :
                    quote = get_live_price(f'{i[0]}.NS')
                    i.append("{:.2f}".format(quote))
                return render_template('maininterface.html', username=username, balance=bal[0], transactions=transactions, search_results=[], message = message , watchlist=watchlist)
            cursor.callproc('sell_stock', [username, stock_symbol, quantity, price])
            query = "SELECT balance FROM client WHERE client_id=:username"
            cursor.execute(query, {'username': username})
            bal = cursor.fetchone()
            query="select * from transaction where client_id=:username order by transaction_date desc"
            cursor.execute(query, {'username': username})
            transactions = cursor.fetchall()
            portfolio = cursor.execute(portfolio_query, {'username': username}).fetchall()
            alterable_portfolio = []
            profit = 0
            invested = 0
            curr_val = 0
            
            for x in portfolio:
                alterable_portfolio.append(list(x))
            print(alterable_portfolio)
            for x in alterable_portfolio:
                if x[4] == None:
                    break;
                quote = get_live_price(f'{x[2]}.NS')
                print("Quote is " + str(quote))
                x[4] = "{:.2f}".format(float(x[4]))
                x.append("{:.2f}".format(quote))
                x.append("{:.2f}".format(x[3]*quote))
                x.append("{:.2f}".format(x[3]*float(x[4])))
                x.append("{:.2f}".format(float(x[6])-float(x[7])))
                profit += float(x[8])
                invested += float(x[7])
                curr_val += float(x[6])
            
            alterable_portfolio.append("{:.2f}".format(profit))
            alterable_portfolio.append(invested)
            alterable_portfolio.append(curr_val)
            alterable_portfolio.append(len(alterable_portfolio)+1)
            # print(alterable_portfolio)
            portfolio = alterable_portfolio
            watchlist = cursor.execute(watchlist_query, {'username': username}).fetchall()
            watchlist_new = watchlist
            watchlist = []
            for x in watchlist_new:
                watchlist.append(list(x))
            for i in watchlist :
                quote = get_live_price(f'{i[0]}.NS')
                i.append("{:.2f}".format(quote))
            con.commit()
            con.close()
            action=''
            message = f"{quantity} shares of {stock_symbol} sold for Rs.{total_cost:.2f}."
            return render_template('maininterface.html', username=username, balance=bal[0], transactions=transactions, search_results=[], message = message, portfolio=portfolio, watchlist=watchlist)
        elif action== 'watchlist' : 
            symbol = request.form['stock_input']
            query = "select * from watchlist where client_id=:username and stock_id=(select stock_id from stock where symbl=:symbol)"
            watchlist = cursor.execute(watchlist_query, {'username': username}).fetchall()
            watchlist_new = watchlist
            watchlist = []
            for x in watchlist_new:
                watchlist.append(list(x))
            for i in watchlist :
                quote = get_live_price(f'{i[0]}.NS')
                i.append("{:.2f}".format(quote))
            if cursor.execute(query, {'username': username, 'symbol': symbol}).fetchone() is  not None:
                return render_template('maininterface.html', username=username, balance=bal[0], transactions=transactions, search_results=[], message = "Stock already in watchlist", portfolio=portfolio, watchlist=watchlist)
            query = '''
                insert into watchlist values (:username, (select stock_id from stock where symbl=:symbol))
                '''        
            cursor.execute(query, {'username': username, 'symbol': symbol})
            con.commit()

            query="select * from transaction where client_id=:username order by transaction_date desc"
            cursor.execute(query, {'username': username})
            transactions = cursor.fetchall()
            portfolio = cursor.execute(portfolio_query, {'username': username}).fetchall()
            alterable_portfolio = []
            profit = 0
            invested = 0
            curr_val = 0
            
            for x in portfolio:
                alterable_portfolio.append(list(x))
            print(alterable_portfolio)
            for x in alterable_portfolio:
                if x[4] == None:
                    break;
                quote = get_live_price(f'{x[2]}.NS')
                print("Quote is " + str(quote))
                x[4] = "{:.2f}".format(float(x[4]))
                x.append("{:.2f}".format(quote))
                x.append("{:.2f}".format(x[3]*quote))
                x.append("{:.2f}".format(x[3]*float(x[4])))
                x.append("{:.2f}".format(float(x[6])-float(x[7])))
                profit += float(x[8])
                invested += float(x[7])
                curr_val += float(x[6])
            
            alterable_portfolio.append("{:.2f}".format(profit))
            alterable_portfolio.append(invested)
            alterable_portfolio.append(curr_val)
            alterable_portfolio.append(len(alterable_portfolio)+1)
            # print(alterable_portfolio)
            portfolio = alterable_portfolio
            watchlist = cursor.execute(watchlist_query, {'username': username}).fetchall()
            watchlist_new = watchlist
            watchlist = []
            for x in watchlist_new:
                watchlist.append(list(x))
            for i in watchlist :
                quote = get_live_price(f'{i[0]}.NS')
                i.append("{:.2f}".format(quote))
            
            con.commit()
            con.close()
            return render_template('maininterface.html', username=username, balance=bal[0], transactions=transactions, search_results=[],portfolio=portfolio, watchlist=watchlist, message=f"{symbol} added to watchlist")
        elif action=='rm_watchlist':
            symbol = request.form['stock_input']
            query = "select * from watchlist where client_id=:username and stock_id=(select stock_id from stock where symbl=:symbol)"
            watchlist = cursor.execute(watchlist_query, {'username': username}).fetchall()
            watchlist_new = watchlist
            watchlist = []
            for x in watchlist_new:
                watchlist.append(list(x))
            for i in watchlist :
                quote = get_live_price(f'{i[0]}.NS')
                i.append("{:.2f}".format(quote))
            if cursor.execute(query, {'username': username, 'symbol': symbol}).fetchone() is None:
                return render_template('maininterface.html', username=username, balance=bal[0], transactions=transactions, search_results=[], message = "Stock not in watchlist", portfolio=portfolio, watchlist=watchlist)
            query = '''
                delete from watchlist where client_id=:username and stock_id=(select stock_id from stock where symbl=:symbol)
                '''
            cursor.execute(query, {'username': username, 'symbol': symbol})
            con.commit()
            watchlist = cursor.execute(watchlist_query, {'username': username}).fetchall()
            watchlist_new = watchlist
            watchlist = []
            for x in watchlist_new:
                watchlist.append(list(x))
            for i in watchlist :
                quote = get_live_price(f'{i[0]}.NS')
                i.append("{:.2f}".format(quote))
            con.commit()
            con.close()
            return render_template('maininterface.html', username=username, balance=bal[0], transactions=transactions, search_results=[], portfolio=portfolio, watchlist=watchlist, message=f"{symbol} removed from watchlist")

            
    return render_template('maininterface.html', username=username, balance=bal[0], transactions=transactions, search_results=[], portfolio=portfolio, watchlist=watchlist)

@app.route('/dashboard/<username>/balance_update', methods=['POST', 'GET'])
def balance_update(username):
    if request.method=='POST':
        amount = float(request.form['balance'])
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
                balance = float(cursor.fetchone()[0])
                cursor.callproc('update_transaction', [username, 'Withdraw', amount])
                con.commit()
                return redirect (url_for('dashboard', username=username, message_balanceupdate='Withdraw successful'))
                # return render_template('maininterface.html', username=username,balance=balance, message_balanceupdate='Withdraw successful')
            except cx_Oracle.DatabaseError as e:
                query = "select balance from client where client_id=:username"
                cursor.execute(query, {'username': username})
                balance = float(cursor.fetchone()[0])
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
    
    query = "insert into order values values ()"
    cursor.execute(query, {'new_quantity': new_quantity, 'username': username, 'stock_id': stock_id})

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

@app.route('/admin/<username>', methods=['POST', 'GET'])
def admin(username, message=None, user=None):
    portfolio_query = '''
        SELECT s.stock_id, s.stock_name, s.symbl, p.quantity, AVG(o.price) as buy_price
        FROM stock s
        INNER JOIN portfolio p ON s.stock_id = p.stock_id
        LEFT JOIN (
            SELECT stock_id, price
            FROM (
                SELECT stock_id, price
                FROM orders
                WHERE client_id = :username AND order_type = 'BUY'
                ORDER BY date_time DESC
            )
            WHERE ROWNUM <= 50
        ) o ON s.stock_id = o.stock_id
        WHERE p.client_id = :username
        GROUP BY s.stock_id, s.stock_name, s.symbl, p.quantity
        ORDER BY s.symbl
        '''
    if request.method=='POST':
        if request.form['action'] == 'search_user':
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="orcl")
            con = cx_Oracle.connect(user="system", password="oracle", dsn=dsn)
            cursor = con.cursor()
            query = "SELECT * FROM client WHERE client_id=:username"
            cursor.execute(query, {'username': request.form['user_name']})
            result = cursor.fetchone()
            portfolio = cursor.execute(portfolio_query, {'username': request.form['user_name']}).fetchall()
            alterable_portfolio = []
            profit = 0
            invested = 0
            curr_val = 0
            
            for x in portfolio:
                alterable_portfolio.append(list(x))
            print(alterable_portfolio)
            for x in alterable_portfolio:
                if x[4] == None:
                    break;
                quote = get_live_price(f'{x[2]}.NS')
                print("Quote is " + str(quote))
                x[4] = "{:.2f}".format(float(x[4]))
                x.append("{:.2f}".format(quote))
                x.append("{:.2f}".format(x[3]*quote))
                x.append("{:.2f}".format(x[3]*float(x[4])))
                x.append("{:.2f}".format(float(x[6])-float(x[7])))
                profit += float(x[8])
                invested += float(x[7])
                curr_val += float(x[6])
            
            alterable_portfolio.append("{:.2f}".format(profit))
            alterable_portfolio.append(invested)
            alterable_portfolio.append(curr_val)
            alterable_portfolio.append(len(alterable_portfolio)+1)
            # print(alterable_portfolio)
            portfolio = alterable_portfolio
            if result:
                return render_template('admin.html', username=username, user=result, portfolio=portfolio)
            else:
                return render_template('admin.html', username=username, message="User not found")
        elif request.form['action'] == 'add':
            user_id = request.form['user_id']
            symbol = request.form['symbol']
            quantity = request.form['quantity']
            quote = get_live_price(f'{symbol}.NS')
            price = "{:.2f}".format(quote)
            price =float(price)
            total_cost = int(quantity) * price
            
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="orcl")
            con = cx_Oracle.connect(user="system", password="oracle", dsn=dsn)
            cursor = con.cursor()
            
            query = "SELECT balance FROM client WHERE client_id=:username"
            cursor.execute(query, {'username': user_id})
            balance = float(cursor.fetchone()[0])
            if total_cost > balance:
                message = "Insufficient funds to make purchase."
                return render_template('admin.html', username=username,modify_message=message)
            cursor.callproc('buy_stock', [user_id, symbol, quantity, price])
            # Add new stock purchase to portfolio
            query = "SELECT stock_id FROM stock WHERE symbl=:stock_symbol"
            cursor.execute(query, {'stock_symbol': symbol})
            stock_id = cursor.fetchone()[0]
            
            query = "SELECT quantity FROM portfolio WHERE client_id=:username AND stock_id=:stock_id"
            cursor.execute(query, {'username': user_id, 'stock_id': stock_id})
            result = cursor.fetchone()
            if result:
                # Stock is already in portfolio, update quantity
                new_quantity = int(result[0]) + int(quantity)
                query = "UPDATE portfolio SET quantity=:new_quantity WHERE client_id=:username AND stock_id=:stock_id"
                cursor.execute(query, {'new_quantity': new_quantity, 'username': user_id, 'stock_id': stock_id})
            else:
                # Stock is not in portfolio, insert new row
                query = "INSERT INTO portfolio (client_id, stock_id, quantity) VALUES (:username, :stock_id, :quantity)"
                cursor.execute(query, {'username': user_id, 'stock_id': stock_id, 'quantity': quantity})
            con.commit()
            con.close()
            message = f"{quantity} shares of {symbol} purchased at Rs.{total_cost:.2f} for {user_id}."
            return render_template('admin.html', username=username,modify_message=message)
        elif request.form['action'] == 'remove':
            user_id = request.form['user_id']
            stock_symbol = request.form['symbol']
            quantity = float(request.form['quantity'])
            quote = get_live_price(f'{stock_symbol}.NS')
            price = "{:.2f}".format(quote)
            price =float(price)    
            total_cost = quantity * price
            
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="orcl")
            con = cx_Oracle.connect(user="system", password="oracle", dsn=dsn)
            cursor = con.cursor()
            
            query = "SELECT balance FROM client WHERE client_id=:username"
            cursor.execute(query, {'username': user_id})
            balance = int(cursor.fetchone()[0])
            query = "SELECT quantity FROM portfolio WHERE stock_id = (select stock_id from stock where symbl=:stock_symbol) and client_id=:username"
            cursor.execute(query, {'stock_symbol': stock_symbol, 'username': user_id})
            quantity_available = cursor.fetchone()

            if quantity_available is None:
                message = f"{user_id} doesn't this stock."
                return render_template('admin.html', username=username,modify_message=message)
            elif int(quantity_available[0])<quantity:
                message = "Not enough shares to sell."
                return render_template('admin.html', username=username,modify_message=message)
            cursor.callproc('sell_stock', [user_id, stock_symbol, quantity, price])
            con.commit()
            con.close()
            message = f"{quantity} shares of {stock_symbol} sold at Rs.{total_cost:.2f} for {user_id}."
            return render_template('admin.html', username=username,modify_message=message)
        elif request.form['action'] == 'user_action':
            action = request.form['user-action']
            user_id = request.form['user_id']
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="orcl")
            con = cx_Oracle.connect(user="system", password="oracle", dsn=dsn)
            cursor = con.cursor()
            if action=='block':
                print("Entered the block")
                query = "SELECT active FROM client WHERE client_id=:username"
                cursor.execute(query, {'username': user_id})
                result = cursor.fetchone()
                if result[0]==0:
                    message = "User already blocked"
                    print(message)
                    con.commit()
                    con.close()
                    return render_template('admin.html', username=username,action_message=message)
                query="update client set active=0 where client_id=:username"
                cursor.execute(query, {'username': user_id})
                message="User blocked"
                print(message)
                con.commit()
                con.close()
                return render_template('admin.html', username=username,action_message=message)
            elif action=='unblock':
                query = "SELECT active FROM client WHERE client_id=:username"
                cursor.execute(query, {'username': user_id})
                result = cursor.fetchone()
                if result[0]==1:
                    message = "User already unblocked"
                    con.commit()
                    con.close()
                    return render_template('admin.html', username=username,action_message=message)
                query="update client set active=1 where client_id=:username"
                cursor.execute(query, {'username': user_id})
                message="User unblocked"
                con.commit()
                con.close()
                return render_template('admin.html', username=username,action_message=message)


                
                
    return render_template('admin.html', username=username, message=message, user=user)

if __name__ == '__main__':
    app.run(debug=True)