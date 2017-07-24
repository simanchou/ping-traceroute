# -*- coding: utf-8 -*-

import ipaddress
import subprocess
import rrdtool
import time
import sqlite3
import os
from sender import Mail, Message
import wechat
import csv
import hashlib

def ip_validation(my_ip):
    try:
        ipaddress.ip_address(my_ip)
        return True
    except:
        return False


def fping(my_target):
    my_command = "fping -i 1000 -q -C20 {}".format(my_target)
    p = subprocess.run("{}".format(my_command), shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    cmd_out = p.stderr.decode("utf8")
    result_time = cmd_out.split(":")[1].split()
    if "-" in result_time:
        result_loss = result_time.count("-") * 5
    else:
        result_loss = 0
    return result_loss, result_time


def create_rrd(rrd_target):
    curl_dir = os.path.split(os.path.realpath(__file__))[0]
    rrd_dir = os.path.join(curl_dir, "static/data", rrd_target, "rrd")
    if not os.path.exists(rrd_dir):
        os.makedirs(rrd_dir)
        print("{} rrd dir successful.".format(rrd_dir))
        os.makedirs(os.path.join(curl_dir, "static/data", rrd_target, "image"))
        print("{} image dir successful.".format(os.path.join(curl_dir, "static/data", rrd_target, "image")))
        os.makedirs(os.path.join(curl_dir, "static/data", rrd_target, "traceroute"))
        print("{} traceroute dir successful.".format(os.path.join(curl_dir, "static/data", rrd_target, "traceroute")))
    if os.path.exists("{}/{}.rrd".format(rrd_dir, rrd_target)):
        print("{}.rrd is exist.".format(rrd_target))
    else:
        cur_time = str(int(time.time()))
        rrd = rrdtool.create('{}/{}.rrd'.format(rrd_dir, rrd_target), '--step', '60', '--start', cur_time,
                             'DS:loss:GAUGE:120:U:U',
                             'DS:time:GAUGE:120:U:U',

                             'RRA:LAST:0.5:1:603',
                             'RRA:LAST:0.5:6:603',
                             'RRA:LAST:0.5:24:603',
                             'RRA:LAST:0.5:288:800')
        try:
            rrd
            print("{}.rrd create successful.".format(rrd_target))
            return 1
        except:
            print(rrdtool.error())
            return 0


def update_rrd(rrd_target):
    curl_dir = os.path.split(os.path.realpath(__file__))[0]
    rrd_dir = os.path.join(curl_dir, "static/data", rrd_target, "rrd")
    rrdfile = "{}/{}.rrd".format(rrd_dir, rrd_target)
    while True:
        start_time = time.time()
        get_result_by_fping = fping(rrd_target)
        r_loss = get_result_by_fping[0]
        print("{} loss is: {}".format(rrd_target, r_loss))
        if r_loss == 100:
            r_time = 0
        else:
            r_time = get_median(get_result_by_fping[1])
        exec_update_rrd = rrdtool.updatev("{}".format(rrdfile),"N:-{}:{}".format(r_loss, r_time))
        try:
            exec_update_rrd
            print("{}Update successful.Loss:{}\t Time:{}".format(rrd_target, r_loss, r_time))
        except:
            print("{}Update fail.".format(rrd_target))
        # '''
        if r_loss:
            tr_save_file = my_tr(rrd_target)
            send_alarm_mail(rrd_target, r_loss, tr_save_file)
            wechat_subject = "[Alarm]{} Loss {}".format(rrd_target, r_loss)
            with open(tr_save_file) as f:
                wechat_content = f.read()
                wechat.send_to_wechat(wechat_subject, wechat_content)
        # '''
        end_time = time.time()
        print(60 - int(end_time - start_time))
        time.sleep(60 - int(end_time - start_time))


def create_graph(rrd_target):
    curl_dir = os.path.split(os.path.realpath(__file__))[0]
    image_dir = os.path.join(curl_dir, "static/data", rrd_target, "image")
    rrd_dir = os.path.join(curl_dir, "static/data", rrd_target, "rrd")
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)
    create_day = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    create_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    title = "{} Ping Delay".format(rrd_target)
    rrdtool.graph("{}/{}.png".format(image_dir, rrd_target), "--start", "-2h", "--vertical-label=Loss(%)|Delay(ms)",
                  "--x-grid", "MINUTE:1:MINUTE:10:MINUTE:10:0:%H:%M",
                  "--alt-y-grid","--alt-autoscale",
                  "--rigid",
                  "--width", "800", "--height", "230", "--title", title,
                  "DEF:r_time={}/{}.rrd:time:LAST:step=120".format(rrd_dir, rrd_target),
                  "DEF:r_loss={}/{}.rrd:loss:LAST:step=120".format(rrd_dir, rrd_target),
                  "LINE1:r_time#00FF00:Delay",
                  "AREA:r_loss#FF0000:Loss",
                  "HRULE:0#000000:Split Line\\r",
                  "CDEF:r_loss_abs=r_loss,-1,/",
                  "COMMENT:\\r",
                  "COMMENT:\\r",
                  "GPRINT:r_time:LAST:Current Delay\: %6.0lf %Sms\l",
                  "GPRINT:r_loss_abs:LAST:Current Loss \: %6.0lf  %%",
                  "COMMENT:LAST UPDATED {} {}\:{}\:{}".format(create_day,
                                                                time.strftime('%H', time.localtime(time.time())),
                                                                time.strftime('%M', time.localtime(time.time())),
                                                                time.strftime('%S', time.localtime(time.time())))
                  )
    print("{}.png create successful.".format(rrd_target))


def create_graph_detail(rrd_target, period):
    grap_setting_dict = {
        "2h": ("2 Hours", "MINUTE:1:MINUTE:10:MINUTE:10:0:%H:%M", 120),
        "1d": ("1 Day", "HOUR:1:HOUR:1:HOUR:2:0:%H:%M", 1200),
        "1w": ("1 Week", "DAY:1:DAY:1:DAY:1:0:%D", 12000),
        "1m": ("1 Month", "DAY:1:DAY:1:DAY:3:0:%D", 120000),
        "1y": ("1 Year", "MONTH:1:MONTH:1:MONTH:1:0:%m", 120000),
    }
    curl_dir = os.path.split(os.path.realpath(__file__))[0]
    image_dir = os.path.join(curl_dir, "static/data", rrd_target, "image")
    rrd_dir = os.path.join(curl_dir, "static/data", rrd_target, "rrd")
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)
    create_day = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    create_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    title = "{} Ping Delay In {}".format(rrd_target, grap_setting_dict[period][0])
    rrdtool.graph("{}/{}_{}.png".format(image_dir, rrd_target, period),
                  "--start", "-{}".format(period), "--vertical-label=Loss(%)|Delay(ms)",
                  "--x-grid", "{}".format(grap_setting_dict[period][1]),
                  "--alt-y-grid","--alt-autoscale",
                  "--rigid",
                  "--width", "800", "--height", "230", "--title", title,
                  "DEF:r_time={}/{}.rrd:time:LAST:step={}".format(rrd_dir, rrd_target, grap_setting_dict[period][2]),
                  "DEF:r_loss={}/{}.rrd:loss:LAST:step={}".format(rrd_dir, rrd_target, grap_setting_dict[period][2]),
                  "LINE1:r_time#00FF00:Delay",
                  "AREA:r_loss#FF0000:Loss",
                  "HRULE:0#000000:Split Line\\r",
                  "CDEF:r_loss_abs=r_loss,-1,/",
                  "COMMENT:\\r",
                  "COMMENT:\\r",
                  "GPRINT:r_time:LAST:Current Delay\: %6.0lf %Sms\l",
                  "GPRINT:r_loss_abs:LAST:Current Loss \: %6.0lf  %%",
                  "COMMENT:LAST UPDATED {} {}\:{}\:{}".format(create_day,
                                                                time.strftime('%H', time.localtime(time.time())),
                                                                time.strftime('%M', time.localtime(time.time())),
                                                                time.strftime('%S', time.localtime(time.time())))
                  )
    print("{}_{}.png create successful.".format(rrd_target, period))



def get_median(data):
    if "-" in data:
        while True:
            data.remove("-")
            if "-" not in data:
                break
    size = len(data)
    if size == 0:
        data[0] = 0
        return data[0]
    else:
        data = sorted([float(item) for item in data])
        if size % 2 == 0:  # 判断列表长度为偶数
            median = (data[size // 2] + data[size // 2 - 1]) / 2
            data[0] = median
        if size % 2 == 1:  # 判断列表长度为奇数
            median = data[(size - 1) // 2]
            data[0] = median
        return "{:.2f}".format(data[0])


def send_alarm_mail(ip_target, ping_loss, tr_save_file):
    print("start to send alarm mail for {}".format(ip_target))
    curl_dir = os.path.split(os.path.realpath(__file__))[0]
    db_file = os.path.join(curl_dir, "p_a_t.db")
    con = sqlite3.connect(db_file)
    cur = con.cursor()
    sql_select = "select * from smtp_server where active=1"
    cur.execute(sql_select)
    smtp_info = cur.fetchone()

    if smtp_info:
        mail = Mail(smtp_info[1],
                    port=smtp_info[2],
                    username=smtp_info[3],
                    password=smtp_info[4],
                    use_ssl=True,
                    fromaddr=smtp_info[3])
        msg = Message("[Alarm]{} loss {}%".format(ip_target, ping_loss))
        receivers = []
        for i in smtp_info[6].split(","):
            receivers.append(i)
        msg.to = receivers
        msg.body = ""
        with open(tr_save_file) as f:
            for i in f.readlines():
                msg.body += i
        mail.send(msg)
        print("{} Alarm mail send successful.Receivers are :{}".format(ip_target, receivers))
    else:
        print("There's no active SMTP server,can't send alarm mail.")


def my_tr(ip_addr):
    curl_dir = os.path.split(os.path.realpath(__file__))[0]
    tr_save_dir = os.path.join(curl_dir, "static/data", ip_addr, "traceroute")
    if not os.path.exists(tr_save_dir):
        os.makedirs(tr_save_dir)
    #curl_time = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime())
    tr_save_file = tr_save_dir + "/" + str(int(time.time())) + ".txt"
    print("{} traceroute file is :{}".format(ip_addr, tr_save_file))
    my_cmd = "mtr --no-dns -c5 -r {} >{}".format(ip_addr, tr_save_file)
    subprocess.run(my_cmd, shell=True)
    print("{} traceroute file save successful.".format(ip_addr))
    return tr_save_file


def del_old_tr_file(ip_addr):
    curl_dir = os.path.split(os.path.realpath(__file__))[0]
    cur_day_in_timestamp = time.mktime(time.strptime(time.strftime("%Y-%m-%d", time.localtime()), "%Y-%m-%d"))
    save_period = 3600 * 24 * 30
    scan_dir = os.path.join(curl_dir, "static/data", ip_addr, "traceroute")
    print(scan_dir)
    if os.path.exists(scan_dir):
        for tr_file in os.listdir(scan_dir):
            if cur_day_in_timestamp - float(tr_file.split(".")[0]) > save_period:
                os.remove("{}/{}".format(scan_dir, tr_file))
                print("{} of {} have saved more than 30 days, delete successful.".format(tr_file, ip_addr))


def csv_reader(csvfile):
    with open(csvfile, newline='') as f:
        data = csv.reader(f)
        csv_header = next(data)
        print(csv_header)
        print("----------")
        data_list = []
        for row in data:
            data_list.append(row)
    return data_list


def create_hash_for_passwd(passwd_str):

    hash = hashlib.sha256()
    hash.update(passwd_str.encode('utf-8'))
    hash_result = hash.hexdigest()
    return hash_result


if __name__ == "__main__":
    my_ip = "111.13.101.208"
    print(ip_validation(my_ip))

    # result = fping(my_ip)
    # print(result)
    # data = result[1]
    # print(get_median(data))

    #print(create_rrd(my_ip))

