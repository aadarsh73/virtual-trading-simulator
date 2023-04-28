# script to load the stock data from the API to the database

import requests
import cx_Oracle

url = "https://twelve-data1.p.rapidapi.com/stocks"

querystring = {"country":"INDIA","exchange":"NSE","format":"json"}

headers = {
	"content-type": "application/octet-stream",
	"X-RapidAPI-Key": "6d91ff0a31msh95476c6bcbd8275p1c07dbjsn52b1a3f55df6",
	"X-RapidAPI-Host": "twelve-data1.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

res = response.json()

dsn = cx_Oracle.makedsn("localhost", 1521, service_name="orcl")
con = cx_Oracle.connect(user="system", password="oracle", dsn=dsn)
cursor = con.cursor()

name_list = []
print(len(res['data'])) 
i=1
for x in res['data']:
    stock_name=x['name']
    stock_symbol=x['symbol']
    if (len(stock_name)>50):
        name_list.append(stock_name)
        continue
    query = "insert into stock values (:stock_id,:stock_name,:stock_symbol)"
    cursor.execute(query, {'stock_id': str(i), 'stock_name': stock_name, 'stock_symbol': stock_symbol })
    i=i+1
    print(i)
con.commit()
print('done')
for k in name_list:
    print(k)
print(len(name_list))
print('done')