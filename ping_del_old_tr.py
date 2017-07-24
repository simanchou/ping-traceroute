import myfunc
import time
import sqlite3
import os

curl_dir = os.path.split(os.path.realpath(__file__))[0]
db_file = os.path.join(curl_dir, "p_a_t.db")
con = sqlite3.connect(db_file)
cur = con.cursor()
cur.execute("select ip from host")
save_period = 3600 * 24 * 30
while True:
    for i in cur.fetchall():
        myfunc.del_old_tr_file(i[0])
    time.sleep(save_period)
