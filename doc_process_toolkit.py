import subprocess
import time


def check_server(port=9998):
    """ Callback type function to let user know server status """

    pid = get_pid(port=port)
    if pid:
        print("Server running on port {0} with pid of {1}".format(port, pid))
    else:
        print("Server not running on port {}".format(port))


def get_pid(port=9998):
    """ Checks Tika server's PID """

    server_pid = subprocess.Popen(
        args=['lsof -i :%s -t' % port],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True
    )
    return server_pid.communicate()[0]


def server_setup_timer(port=9998):
    """ Checks for server to start with a loop """

    for i in range(10):
        time.sleep(1)
        if get_pid(port):
            print("Server Started !")
            break
        else:
            print("Waited %s second(s)" % i)


def stat_tika_server(port=9998):
    """ Starts Tika server """

    pid = get_pid(port)
    if pid:
        print("Process already running on port %s" % port)
        return
    subprocess.Popen(
        args=['java -jar tika-app-1.7.jar --server --text --port %s' % port],
        shell=True)
    server_setup_timer(port)


def stop_tika_server(port=9998):
    """ Kills Tika server """

    pid = get_pid(port)
    if pid:
        subprocess.Popen(
            args=['kill -9 %s' % pid],
            stderr=subprocess.STDOUT,
            shell=True)
    else:
        print("Server not running on port %s" % port)


if __name__ == '__main__':
    stat_tika_server()
    check_server()
    stop_tika_server()
