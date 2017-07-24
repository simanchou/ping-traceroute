import myfunc
import sqlite3
import multiprocessing
import os

curl_dir = os.path.split(os.path.realpath(__file__))[0]
db_file = os.path.join(curl_dir, "p_a_t.db")
con = sqlite3.connect(db_file)
cur = con.cursor()
cur.execute("select ip from host")
jobs = []
for i in cur.fetchall():
    print(i[0])
    p = multiprocessing.Process(target=myfunc.update_rrd, args=(i[0], ))
    p.daemon = True
    jobs.append(p)
    p.start()
for j in jobs:
    j.join()
