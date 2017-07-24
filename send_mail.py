from sender import Mail, Message
import sqlite3
import os


def send_alarm_mail(ip_target, ping_loss):
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
        with open("{}.txt".format(ip_target)) as f:
            for i in f.readlines():
                msg.body += i
        mail.send(msg)
        print("Alarm mail send successful.Receivers are :{}".format(receivers))
    else:
        print("There's no active SMTP server,can't send alarm mail.")


if __name__ == "__main__":
    ip_target = "45.64.186.252"
    ping_loss = "20"
    send_alarm_mail(ip_target, ping_loss)