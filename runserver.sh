#!/bin/bash
py_env="/home/simanchou/rrdtool-test/bin/python"
app_dir=$(cd "$(dirname "$0")"; pwd)
apps="pat.py ping_create_rrd.py ping_update_rrd.py ping_del_old_tr.py"

function start()
{
	for app in $apps
	do
		nohup $py_env $app_dir"/"$app >/dev/null 2>&1 &
		echo $app" start successful."
	done
}

function stop()
{
	for app in $apps
	do
		proc_pid=`(ps aux | grep $app | grep -v "grep" | awk '{print $2}')`
		for s_pid in $proc_pid
		do
			kill -9 $s_pid
		done
	done
}

function restart_collector()
{
    for app_c in "ping_create_rrd.py ping_update_rrd.py"
	do
		proc_c=`(ps aux | grep $app_c | grep -v "grep" | awk '{print $2}')`
		for s_pid_c in $proc_c
		do
			kill -9 $s_pid_c
		done
	done

	for app_d in "ping_create_rrd.py ping_update_rrd.py"
	do
	    nohup $py_env $app_dir"/"$app_d >/dev/null 2>&1 &
		echo $app_d" start successful."
	done
}

case "$1" in
	"start")
	start
	;;
	"stop")
	stop
	;;
	"restart")
	stop
	start
	;;
	"restart_collector")
	restart_collector
	;;
	*)
	echo "Usage: $0 {start|stop|restart}"
	;;
esac
