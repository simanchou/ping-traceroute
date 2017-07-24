# _*_coding:utf-8 _*_


import urllib.request, urllib.parse, urllib.error
import json
import sys
import simplejson
import sqlite3
import os


def send_to_wechat(subject, content):
    curl_dir = os.path.split(os.path.realpath(__file__))[0]
    db_file = os.path.join(curl_dir, "p_a_t.db")
    con = sqlite3.connect(db_file)
    cur = con.cursor()
    cur.execute('SELECT * FROM wechat where active=1')
    wechat_info = cur.fetchone()
    if wechat_info:
        if wechat_info[5]:
            corpid = wechat_info[1]
            corpsecret = wechat_info[2]
            agentid = wechat_info[3]
            toparty = wechat_info[4]
            gettoken_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=' + corpid + '&corpsecret=' + corpsecret
            # print(gettoken_url)
            try:
                token_file = urllib.request.urlopen(gettoken_url)
            except urllib.error.HTTPError as e:
                print(e.code)
                print(e.read().decode("utf8"))
                sys.exit()
            token_data = token_file.read().decode('utf-8')
            token_json = json.loads(token_data)
            list(token_json.keys())
            token = token_json['access_token']

            send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=' + token
            send_values = {
                "toparty": toparty,  # 企业号中的部门id。
                "msgtype": "text",  # 消息类型。
                "agentid": agentid,  # 企业号中的应用id。
                "text": {
                    "content": subject + '\n' + content
                },
                "safe": "0"
            }
            send_data = simplejson.dumps(send_values, ensure_ascii=False).encode('utf-8')
            send_request = urllib.request.Request(send_url, send_data)
            response = json.loads(urllib.request.urlopen(send_request).read().decode('utf-8'))
            if response["errcode"] == 0:
                print("Alarm send to WeChat successful.")
            else:
                print(response)
        else:
            print("There's no active WeChat.Alarm data won't send to WeChat.")
    else:
        print("There's no active WeChat.Alarm data won't send to WeChat.")




if __name__ == '__main__':
    subject = "[Alarm]this is a test"
    content = '''
    Host:127.0.0.1 Loss 20%
    Traceroute file Click here to check.
    <a href=\"http://www.13322.com\">路由跟踪结果</a>
    '''

    send_to_wechat(subject, content)



