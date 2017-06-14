#!/usr/bin/python
# coding: utf8

import requests
import sqlite3
import os
import threading
from Queue import Queue
import logging


VUL_URL = 'http://ip:8080/'   # 地址
THREAD_NUM = 10               # 线程数


class MyThread(threading.Thread):
    def __init__(self, func, args, name=''):
        threading.Thread.__init__(self)
        self.name = name
        self.func = func
        self.args = args

    def run(self):
        self.func(self.args)


def download(queue):
    while True:
        info = get_url(queue)
        tp = to_download_url(info)
        download_url = tp[1]
        save_path = tp[0]
        if download_url:
            d = requests.get(download_url)
            if d.status_code != 404:
                with open(save_path, "wb") as content:
                    content.write(d.content)


def to_download_url(info):
    real_path = info[0]
    check_sum = info[1]
    if check_sum:
        if '/' in real_path:
            real_path = real_path.replace('/', '\\')
            if not os.path.exists(real_path[:real_path.rfind('\\')]):
                try:
                    os.makedirs(real_path[:real_path.rfind('\\')])
                except:
                    logging.error('create directory failed.')
        download_url = VUL_URL + ".svn/pristine/" + check_sum[6:8] + "/" + check_sum[6:] + ".svn-base"
        return real_path, download_url
    else:
        return None, None


def get_url(queue):
    if queue.qsize() == 0:
        exit()
    logging.warning(' There are {num} left , downloading ...'.format(num=queue.qsize()))
    return queue.get()


def main():

    svn = ".svn/wc.db"
    r = requests.get(VUL_URL + svn)
    with open("vul.db", "wb") as code:
        code.write(r.content)
    # 从数据库将信息导入list
    conn = sqlite3.connect("vul.db")
    info_list = list(conn.execute("SELECT local_relpath, checksum from NODES;"))
    q = Queue()
    for each in info_list:
        q.put(each)

    print 'start to download source file ...'
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    threads = []
    for i in xrange(THREAD_NUM):
        t = MyThread(download, q)
        threads.append(t)

    for j in threads:
        j.start()

if __name__ == '__main__':
    main()
