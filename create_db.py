import sqlite3

con = sqlite3.connect('zde_db.sqlite')
cur = con.cursor()
with open('create_db.sql', 'r') as f:
    text = f.read()
cur.executescript(text)
cur.close()
con.close()
