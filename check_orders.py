import sqlite3

conn = sqlite3.connect('orders.db')
c = conn.cursor()
for row in c.execute('SELECT * FROM orders'):
    print(row)
conn.close()