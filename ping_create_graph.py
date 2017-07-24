import myfunc
import sqlite3
import time
import os


curl_dir = os.path.split(os.path.realpath(__file__))[0]
db_file = os.path.join(curl_dir, "p_a_t.db")
con = sqlite3.connect(db_file)
cur = con.cursor()
cur.execute("select ip from host")

for i in cur.fetchall():
    myfunc.create_rrd(i[0])
