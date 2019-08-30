import socket
import threading
import signal
import time
import logging

HOST = ''
PORT = 3118
client_list = []   # list of tuple, (socket, roomNumber, name)
serverFlag = True
serverSocket = None

logging.basicConfig(filename=u'log.txt',
                    filemode='w',
                    format=u'%(levelname)s %(asctime)s :: %(message)s',
                    level=logging.DEBUG)


def print_and_log(message):
    print(message)
    logging.info(message)


def server_listener():
    global serverSocket
    global serverFlag
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind((HOST, PORT))
    serverSocket.listen(100)

    print_and_log("server is listening")

    while serverFlag:
        try:
            serverSocket.settimeout(0.5)
            conn, addr = serverSocket.accept()
            threading.Thread(target=client_listener, args=(conn, addr)).start()
        except socket.timeout:
            pass
        except socket.error as e:
            text = str(e)
            print_and_log(text)
    print_and_log("server END")
    return


def client_listener(conn, addr):
    global serverFlag
    client_connected = True
    room_number = -1
    username = ""
    while serverFlag:
        try:
            data = conn.recv(1024)
            data = data.decode()
            if data:
                # 메세지 종류
                # ※※user  user가 서버에 처음 접속요청 (서버가 받음)
                # ※x. x번째 채팅방에 입장(서버가 받음)
                # ※1. 새로운 유저 입장(클라가 받음)
                # ※2. 유저 나감(클라)
                # ※3. 유저 목록(클라)
                # ※0. 일반 메세지(클라)
                if data[0] == '※':
                    if data[1] == '※':
                        username = data[2:]
                        send_all_userlist(conn)
                        print_and_log("client {} enter waiting room".format(username))
                    else:
                        room_number = data[1]
                        client_list.append((conn, room_number, username))

                        # 방의 다른 유저들에게 유저가 들어옴을 알리기
                        print_and_log("client {} enter room{}".format(username, room_number))
                        message_to_send = "※1" + username
                        broadcast(message_to_send, conn, room_number)

                        # 처음 방에 들어온 유저에게는 이미 방에 있는사람 목록 보내주기
                        send_userlist(conn, room_number)
                else:
                    message_to_send = "※0<" + username + "> " + data
                    broadcast(message_to_send, conn, room_number)
            else:
                client_connected = False
                client_leave(conn, username, room_number)
        except socket.error as e:
            client_connected = False
            print_and_log(str(e))
            client_leave(conn, username, room_number)
        if not client_connected:
            break


def broadcast(message, conn, room):
    message = message.encode()
    for client in client_list:
        if client[1] == room:
            try:
                client[0].send(message)
            except socket.error:
                client[0].close()
                remove(conn)


def send_userlist(conn, room):
    message = "※3"
    for client in client_list:
        if client[1] == room:
            message += client[2]
            message += "|"
    conn.send(message.encode())


def send_all_userlist(conn):
    message = ""
    for room in range(10):
        message += "※"
        message += str(room)
        for client in client_list:
            if client[1] == str(room):
                message += client[2]
                message += "|"
    conn.send(message.encode())


def client_leave(conn, username, room):
    if room == -1:
        print_and_log("client {} leave waiting room".format(username))
    else:
        print_and_log("client {} leave room{}".format(username, room))
        remove(conn)
        message_to_send = "※2" + username
        broadcast(message_to_send, conn, room)
    print("current user list: ", client_list)


def remove(conn):
    for item in client_list:
        if item[0] == conn:
            client_list.remove(item)


def signal_handler(signal, frame):
    print_and_log("signal caught")
    global serverFlag
    serverFlag = False
    for client in client_list:
        client[0].close()


def main():
    signal.signal(signal.SIGINT, signal_handler)
    server = threading.Thread(target=server_listener)
    server.start()
    print_and_log("server is running. Ctrl+C for exit")
    while serverFlag:
        time.sleep(1)


if __name__ == '__main__':
    main()
