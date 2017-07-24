import myfunc


ip = "qq.com"
peroid = ["2h", "1d", "1w", "1m", "1y"]
for i in peroid:
    myfunc.create_graph_test(ip, i)


