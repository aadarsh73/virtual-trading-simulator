# importing module
import cx_Oracle
 
# Create a table in Oracle database
try:
 
    # Connect as sysdba
    dsn = cx_Oracle.makedsn("localhost", 1521, service_name="orcl")
    con = cx_Oracle.connect(user="system", password="oracle", dsn=dsn)
    # con = cx_Oracle.connect(user="sys", password="oracle", dsn=dsn, mode=cx_Oracle.SYSDBA)

    print(con.version)
 
    # Now execute the sqlquery
    cursor = con.cursor()
 
    #Creating a table employee
    cursor.execute(
        "create table employee(empid integer primary key, name varchar2(30), salary number(10, 2))")
 
    print("Table Created successfully")

    #Inserting data into the table
    cursor.execute(
        "insert into employee values(5, 'Yash', 65000)")
    print("Details entered successfully!")

    con.commit()

    print(cursor.execute("SELECT * FROM employee"))

 
except cx_Oracle.DatabaseError as e:
    print("There is a problem with Oracle", e)
 
# by writing finally if any error occurs
# then also we can close the all database operation
finally:
    if cursor:
        cursor.close()
    if con:
        con.close()