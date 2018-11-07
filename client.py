__author__ = 'larry'
__date__ = '2018/11/6 9:00'

import threading
import socket
import time
import sys


class Client():
    def __init__(self, host, port=8000, timeout=1):
        self.__host = host
        self.__port = port
        self.__timeout = timeout
        self.__buffer_size = 1024
        # 用于判断当前client是否退出
        self.__flag = 1
        self.client = None
        self.__lock = threading.Lock()

    @property
    def flag(self):
        return self.__flag

    @flag.setter
    def flag(self, new_num):
        self.__flag = new_num

    def __connect(self):
        # 建立连接
        client = socket.socket()
        # 设置非阻塞
        client.setblocking(False)
        # 设置超时时间
        client.settimeout(self.__timeout)

        server_host = (self.__host, self.__port)
        try:
            client.connect(server_host)
        except:
            raise
        return client

    def send_msg(self):
        if not self.client:
            return
        while True:
            time.sleep(0.1)
            data = sys.stdin.readline().strip()
            if data.lower() == "exit":
                with self.__lock:
                    self.__flag = 0
                break
            self.client.sendall(data.encode("utf8"))

        return

    def recv_msg(self):
        if not self.client:
            return
        while True:
            data = None
            with self.__lock:
                if not self.__flag:
                    print("Bye~")
                    break
            try:
                data = self.client.recv(self.__buffer_size)
            except socket.timeout:
                continue
            except:
                raise
            if data:
                print("%s\n" % data)
                time.sleep(0.1)

        return

    def run(self):
        # 获取连接
        self.client = self.__connect()

        send_thread = threading.Thread(target=self.send_msg)
        recv_thread = threading.Thread(target=self.recv_msg)
        send_thread.start()
        recv_thread.start()
        send_thread.join()
        recv_thread.join()
        self.client.close()


if __name__ == "__main__":
    Client("localhost").run()

