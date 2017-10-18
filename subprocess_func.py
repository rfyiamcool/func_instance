# -*- coding:utf-8 -*-
import time
import subprocess
import fcntl
import os
from threading import Timer


class TimeoutCmdError(Exception):
    pass


def external_cmd(cmd, msg_in=''):
    try:
        proc = subprocess.Popen(cmd,
                                shell=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        stdout_value, stderr_value = proc.communicate(msg_in)
        return proc, stdout_value.rstrip("\n"), stderr_value.rstrip("\n")
    except ValueError:
        return proc, None, None


def command_poll_timeout(cmd, timeout=10):
    p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    t_beginning = time.time()
    seconds_passed = 0
    while True:
        if p.poll() is not None:
            break
        seconds_passed = time.time() - t_beginning
        if timeout and seconds_passed > timeout:
            p.terminate()
            return None, None, None
    #        raise TimeoutCmdError()
        time.sleep(0.01)
    return p, p.stdout.read().rstrip("\n"), p.stderr.read().rstrip("\n")


def command_timeout(cmd, timeout=10):
    p = stdout = stderr = None
    kill = lambda process: process.kill()
    p = subprocess.Popen(cmd,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)

    my_timer = Timer(timeout, kill, [p])

    try:
        my_timer.start()
        stdout, stderr = p.communicate()
    finally:
        my_timer.cancel()
    return p, stdout, stderr


def command_poll(cmd, deal, deal_error):
    p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=False)
    fl = fcntl.fcntl(p.stdout.fileno(), fcntl.F_GETFL)
    fcntl.fcntl(p.stdout.fileno(), fcntl.F_SETFL, fl | os.O_NONBLOCK)

    while True:
        if p.poll() is not None:
            if p.returncode:
                deal_error()
            break
        try:
            out = os.read(p.stderr.fileno(), 1024)
            deal(out)
        except Exception, e:
            continue