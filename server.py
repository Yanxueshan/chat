__author__ = 'larry'
__date__ = '2018/11/6 9:00'

'''
    server担任的是一个转发的角色，client与client之间是不能相互通信的
    
    实现思路：
        1、通过select监听多个socket
        

'''


import socket
import select
import time
import queue
from queue import Queue
import logging


class Server():
    def __init__(self, host="0.0.0.0", port=8000, timeout=2, client_nums=10):
        self.__host = host
        self.__port = port
        self.__timeout = timeout
        self.__client_nums = client_nums
        self.__buffer_size = 1024

        self.server = socket.socket()
        self.server.setblocking(False)
        self.server.settimeout(self.__timeout)
        self.host = (self.__host, self.__port)

        try:
            self.server.bind(self.host)
            self.server.listen(self.__client_nums)
        except:
            raise

        # select 接收文件描述符列表
        self.inputs = [self.server]
        # select 输出文件描述符列表
        self.outputs = []
        # 消息队列
        self.message_queues = {}
        self.client_info = {}

    def run(self):
        while True:
            # 对文件描述符进行监听
            readable, writable, exceptional = select.select(self.inputs, self.outputs, self.inputs)

            for s in readable:
                # 有新客户端来连接
                if s is self.server:
                    connection, client_address = s.accept()
                    print("%s connected..." % str(client_address))

                    # 设置连接为非阻塞
                    connection.setblocking(False)
                    # 将客户端加入到监听列表中
                    self.inputs.append(connection)
                    # 将client信息保存在client_info中
                    self.client_info[connection] = str(client_address)
                    # 为每个client建立一个消息队列
                    self.message_queues[connection] = Queue()
                # 有client发消息过来
                else:
                    data = ""
                    try:
                        data = s.recv(self.__buffer_size)
                    except:
                        err_msg = "Client Error!"
                        logging.error(err_msg)
                    if data:
                        # 对data进行格式化, 方便告知其他客户端是谁发送的消息以及是什么时候发送的消息
                        data = "%s %s say: %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), self.client_info[s], str(data))
                        self.message_queues[s].put(data)
                        # 如果当前客户端要发送消息（读写分离）
                        if s not in self.outputs:
                            self.outputs.append(s)
                    # data不存在，表示当前客户端断开连接
                    else:
                        print("Client:%s closed" % self.client_info[s])
                        # 清除当前客户端信息
                        if s in self.outputs:
                            self.outputs.remove(s)
                            self.inputs.remove(s)
                            s.close()
                            del self.message_queues[s]
                            del self.client_info[s]


            for s in writable:
                # 将收到的消息发送出去
                try:
                    # 从消息队列中获取当前client要发送的数据,非阻塞获取
                    next_msg = self.message_queues[s].get_nowait()
                except queue.Empty:
                    # 消息队列为空，表示当前客户端已经断开连接
                    err_msg = "Output Queue is Empty!"
                    self.outputs.remove(s)
                # 消息发送时关闭了客户端，readable和writable同时有数据，message_queues会报Keyerror错误
                except Exception as e:
                    err_msg = "Send Data Error! Error_Msg: %s" % str(e)
                    logging.error(err_msg)
                    if s in self.outputs:
                        self.outputs.remove(s)
                else:
                    for client in self.client_info:
                        if client is not s:
                            try:
                                client.sendall(next_msg.encode("utf8"))
                            # 如果发送失败就关闭
                            except Exception as e:
                                err_msg = "Send Data to %s Error, Error_Msg:%s" % (str(self.client_info[client]), e)
                                logging.error(err_msg)
                                print("Client %s Close Error") % str(self.client_info[client])
                                if client in self.inputs:
                                    self.inputs.remove(client)
                                if client in self.outputs:
                                    self.outputs.remove(client)
                                if client in self.message_queues:
                                    del self.message_queues[client]
                                    del self.client_info[client]
            for s in exceptional:
                logging.error("Client: %s Close Error" % s)
                if s in self.inputs:
                    self.inputs.remove(s)
                if s in self.outputs:
                    self.outputs.remove(s)
                if s in self.message_queues:
                    del self.message_queues[s]
                    del self.client_info[s]


if __name__ == "__main__":
    Server().run()
