# -*- coding:utf-8 -*-
# Author:Siman Chou
# E-mail:2603690088@qq.com
# Web Site:www.simanchou.com
from flask import Flask, request, render_template, session, redirect, url_for, flash
import sqlite3
import myfunc
import os
import time
import subprocess
import shutil


app = Flask(__name__)
app.debug = True
app.config.update(dict(
    SECRET_KEY='development key',
))

curl_dir = os.path.split(os.path.realpath(__file__))[0]
db_file = os.path.join(curl_dir, "p_a_t.db")

@app.route('/')
def index():
    con = sqlite3.connect(db_file)
    cur = con.cursor()
    # create menu on left
    sql_select = "SELECT node FROM host GROUP BY node"
    cur.execute(sql_select)
    node_list = []
    for i in cur.fetchall():
        node_list.append(i[0])
    host_dict = {}
    for i in node_list:
        sql_select = "SELECT ip FROM host WHERE node='{}'".format(i)
        cur.execute(sql_select)
        host_list = []
        for j in cur.fetchall():
            for k in j:
                host_list.append(k)
        host_dict[i] = host_list
    # show graph title on right
    query_host = request.args.get("target")
    query_host_pic_url = "static/data/{}/image/{}_2h.png".format(query_host, query_host)
    query_host_node = ""
    print("Query host:{}".format(query_host))

    # show traceroute under graph on right

    tr_files_list = []
    tr_file_display_dict = {}
    tr_files_url_dict = {}

    if query_host:
        # show graph under title on right
        #myfunc.create_graph(query_host)
        graph_period = ["2h", "1d", "1w", "1m", "1y"]
        for period in graph_period:
            myfunc.create_graph_detail(query_host, period)
        cur.execute("SELECT node FROM host WHERE ip='{}'".format(query_host))
        query_host_node = cur.fetchone()[0]
        print(query_host_node)

        scan_tr_dir = os.path.join(curl_dir, "static/data", query_host, "traceroute")
        tr_files_list = os.listdir(scan_tr_dir)
        tr_files_list.sort()
        tr_files_list.reverse()
        tr_file_display_dict = {}
        tr_files_url_dict = {}
        for tr_file in tr_files_list:
            tr_file_display_name = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(int(tr_file.split(".")[0])))
            tr_file_display_dict[tr_file] = tr_file_display_name
            tr_file_path = os.path.join("static/data", query_host, "traceroute", tr_file)
            tr_files_url_dict[tr_file] = tr_file_path
        print(tr_file_display_dict)
        print(tr_files_url_dict)

    return render_template('index.html', node_list=node_list, host_dict=host_dict, query_host=query_host,
                           query_host_node=query_host_node, query_host_pic_url=query_host_pic_url,
                           tr_files_list=tr_files_list, tr_file_display_dict=tr_file_display_dict,
                           tr_files_url_dict=tr_files_url_dict)


@app.route('/graph')
def graph():
    if request.args.get("host"):
        query_host = request.args.get("host")
        print("this is detail for {}".format(query_host))
        con = sqlite3.connect(db_file)
        cur = con.cursor()
        sql_select = "SELECT node FROM host GROUP BY node"
        cur.execute(sql_select)
        node_list = []
        for i in cur.fetchall():
            node_list.append(i[0])
        host_dict = {}
        for i in node_list:
            sql_select = "SELECT ip FROM host WHERE node='{}'".format(i)
            cur.execute(sql_select)
            host_list = []
            for j in cur.fetchall():
                for k in j:
                    host_list.append(k)
            host_dict[i] = host_list
        cur.execute("SELECT node FROM host WHERE ip='{}'".format(query_host))
        query_host_node = cur.fetchone()[0]

        return render_template('graph.html', node_list=node_list, host_dict=host_dict, query_host= query_host,
                               query_host_node=query_host_node)
    else:
        return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    con = sqlite3.connect(db_file)
    cur = con.cursor()
    if request.method == 'POST':
        cur.execute("select passwd from user where username='{}'".format(request.form['username']))
        user_passwd = cur.fetchone()[0]
        if myfunc.create_hash_for_passwd(request.form['password']) != user_passwd:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('index'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('login'))


@app.route('/admin_host', methods=['GET', 'POST'])
def admin_host():
    if request.args.get("pageid"):
        page_id = request.args.get("pageid")
        display_in_one_page = 10
        con = sqlite3.connect(db_file)
        cur = con.cursor()
        cur.execute("select count(*) from host")
        hosts_count = int(cur.fetchone()[0])
        if hosts_count % display_in_one_page:
            pages = hosts_count // display_in_one_page + 2
        else:
            pages = hosts_count // display_in_one_page + 1
        page_url_list = [i for i in range(1, pages)]
        if page_id == "all":
            cur.execute("select * from host")
            hosts = cur.fetchall()
            return render_template('admin_host.html', hosts=hosts, page_url_list=page_url_list)
        else:
            offset = (int(page_id) - 1) * display_in_one_page
            cur.execute("SELECT * FROM host limit {} offset {}".format(display_in_one_page, offset))
            hosts = cur.fetchall()
            return render_template('admin_host.html', hosts=hosts, page_url_list=page_url_list)
    else:
        con = sqlite3.connect(db_file)
        cur = con.cursor()
        cur.execute("SELECT * FROM host")
        hosts = cur.fetchall()
        if request.method == 'POST':
            if 'add' in request.form.values():
                if myfunc.ip_validation(request.form['input_h']):
                    cur.execute("select ip from host where ip='{}'".format(request.form['input_h']))
                    if cur.fetchone():
                        print("{} is already exist.".format(request.form['input_h']))
                        flash(u"{} is already exist.".format(request.form['input_h']), "ip_exist")
                        return redirect(url_for('admin_host', pageid=1))
                    else:
                        sql_insert_host = "insert into host(node,ip) values('{}', '{}')".format(
                            request.form['input_l'],
                            request.form['input_h']
                        )
                        cur.execute(sql_insert_host)
                        con.commit()
                        flash(u"{} add successful.".format(request.form['input_h']), "add_ip")
                        return redirect(url_for('admin_host', pageid=1))
                else:
                    print("{} is not a valid ip.".format(request.form['input_h']))
                    flash(u"{} is not a valid ip.".format(request.form['input_h']), "valid_ip")
                    return redirect(url_for('admin_host', pageid=1))
            elif 'upload' in request.form.values():
                print("this is upload test")
                csvfile = request.files['file']
                csvfile_save_name = str(int(time.time())) + ".csv"
                csvfile.save(os.path.join(curl_dir, "tmp", csvfile_save_name))
                host_from_csv_add_success = []
                host_from_csv_exist = []
                for i in myfunc.csv_reader(os.path.join(curl_dir, "tmp", csvfile_save_name)):
                    if myfunc.ip_validation(i[1]):
                        cur.execute("select ip from host where ip='{}'".format(i[1]))
                        if cur.fetchone():
                            print("{} is already exist.".format(i[1]))
                            host_from_csv_exist.append(i[1])
                            #flash(u"{} is already exist.".format(i[1]), "ip_exist")
                            #return redirect(url_for('admin_host', pageid=1))
                        else:
                            try:
                                cur.execute("insert into host(node,ip) values('{}', '{}')".format(i[0], i[1]))
                                host_from_csv_add_success.append(i[1])
                                print("Location:{}\tHost:{} add successful.".format(i[0], i[1]))
                            except:
                                print("Location:{}\tHost:{} add fail.".format(i[0], i[1]))
                con.commit()
                os.remove(os.path.join(curl_dir, "tmp", csvfile_save_name))
                flash(u"{} from csv file have add successful.".format(host_from_csv_add_success), "add_ip")
                flash(u"{} from csv file are already exist.".format(host_from_csv_exist), "ip_exist")
                return redirect(url_for('admin_host', pageid=1))
            elif 'delete' in request.form.values():
                for del_id in request.form.getlist("select_ip"):
                    cur.execute("select ip from host where id={}".format(del_id))
                    del_ip = cur.fetchone()[0]
                    try:
                        shutil.rmtree(os.path.join(curl_dir, "static/data", del_ip))
                        print("{} delete successful.".format(os.path.join("static/data", del_ip)))
                    except:
                        print("{} delete fail.There's no such file.".format(os.path.join("static/data", del_ip)))
                    cur.execute("delete from host where id={}".format(del_id))
                con.commit()
                flash(u"Hosts have delete successful.", "del_ip")
                return redirect(url_for('admin_host', pageid=1))
            elif 'confirm' in request.form.values():
                my_command = "sh runserver.sh restart_collector"
                p = subprocess.run("{}".format(my_command), shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
                cmd_out = p.stdout.decode("utf8")
                if "successful" in cmd_out:
                    flash(u"Collector restart successful.", "restart_ok")
                return redirect(url_for('admin_host', pageid=1))
        return render_template('admin_host.html', hosts=hosts)


@app.route('/admin_smtp', methods=['GET', 'POST'])
def admin_smtp():
    con = sqlite3.connect(db_file)
    cur = con.cursor()
    cur.execute("SELECT * FROM smtp_server")
    smtp_servers = cur.fetchall()
    if request.method == 'POST':
        if 'add' in request.form.values():
            sql_insert_smtp = "insert into smtp_server(server,port,username,passwd,active,recevier) values('{}','{}','{}','{}','{}','{}')".format(
                request.form['input_h'],
                request.form['input_po'],
                request.form['input_u'],
                request.form['input_pa'],
                request.form['type_list'],
                request.form['input_r'],
            )
            cur.execute(sql_insert_smtp)
            con.commit()
            return redirect(url_for('admin_smtp'))
        elif 'del' in request.form.values():
            cur.execute("delete from smtp_server where id={}".format(request.form['radio_id']))
            con.commit()
            return redirect(url_for('admin_smtp'))
    return render_template('admin_smtp.html', smtp_servers=smtp_servers)


@app.route('/admin_wechat', methods=['GET', 'POST'])
def admin_wechat():
    con = sqlite3.connect(db_file)
    cur = con.cursor()
    cur.execute("SELECT * FROM wechat")
    wechat_api = cur.fetchall()
    if request.method == 'POST':
        if 'add' in request.form.values():
            sql_insert_we = "insert into wechat(corpid,corpsecret,agentid,toparty,active) values('{}','{}','{}','{}','{}')".format(
                request.form['input_cid'],
                request.form['input_cs'],
                request.form['input_aid'],
                request.form['input_to'],
                request.form['type_list'],
            )
            cur.execute(sql_insert_we)
            con.commit()
            return redirect(url_for('admin_wechat'))
        elif 'del' in request.form.values():
            cur.execute("delete from wechat where id={}".format(request.form['radio_id']))
            con.commit()
            return redirect(url_for('admin_wechat'))
    return render_template('admin_wechat.html', wechat_api=wechat_api)


@app.route('/admin_user', methods=['GET', 'POST'])
def admin_user():
    con = sqlite3.connect(db_file)
    cur = con.cursor()
    cur.execute("SELECT * FROM user")
    users = cur.fetchall()
    if request.method == 'POST':
        if 'add' in request.form.values():
            sql_insert_user = "insert into user(username,passwd) values('{}', '{}')".format(
                request.form['input_u'],
                myfunc.create_hash_for_passwd(request.form['input_p'])
            )
            cur.execute(sql_insert_user)
            con.commit()
            return redirect(url_for('admin_user'))
        elif 'del' in request.form.values():
            cur.execute("delete from user where id={}".format(request.form['radio_id']))
            con.commit()
            return redirect(url_for('admin_user'))
    return render_template('admin_user.html', users=users)


@app.route('/edit_user', methods=['GET', 'POST'])
def edit_user():
    if request.args.get("userid"):
        user_id = request.args.get("userid")
        con = sqlite3.connect(db_file)
        cur = con.cursor()
        cur.execute("SELECT username,passwd FROM user where id='{}'".format(user_id))
        user_info = cur.fetchone()
        user_name = user_info[0]
        return render_template('edit_user.html', user_name=user_name)
    else:
        if request.method == 'POST':
            user_name = request.form['input_u']
            con = sqlite3.connect(db_file)
            cur = con.cursor()
            cur.execute("SELECT username,passwd FROM user where username='{}'".format(user_name))
            user_info = cur.fetchone()
            user_old_passwd = user_info[1]
            input_old_passwd = myfunc.create_hash_for_passwd(request.form['input_op'])
            if user_old_passwd == input_old_passwd:
                if request.form['input_np'] == request.form['input_npa']:
                    cur.execute("update user set passwd='{}' where username='{}'".format(
                        myfunc.create_hash_for_passwd(request.form['input_np']),
                        user_name
                    ))
                    con.commit()
                    print("{}'s passwd update successful.".format(user_name))
                    return redirect(url_for('admin_user'))
                else:
                    print("you don't input the same passwd.")
                    return redirect(url_for('admin_user'))
            else:
                print("you must input correct old passwd.")
                return redirect(url_for('admin_user'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
