import socket
import threading
import signal
import time
import logging

HOST = ''
PORT = 3118
client_list = []   # list of tuple, (scoket, roomNumber, name)
serverFlag = True
serverSocket = None

logging.basicConfig(filename=u'log.txt',
                    filemode='w',
                    format=u'%(levelname)s %(asctime)s :: %(message)s',
                    level=logging.DEBUG)

def printAndLog(message):
    print(message)
    logging.info(message)

def serverListener():
    global serverSocket
    global serverFlag
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind((HOST, PORT))
    serverSocket.listen(100)

    printAndLog("server is listening")

    while serverFlag:
        try:
            serverSocket.settimeout(0.5)
            conn, addr = serverSocket.accept()
            threading.Thread(target=clientListener, args=(conn, addr)).start()
        except socket.timeout:
            pass
        except Exception:
            text = Exception.message
            print(text)
    printAndLog("server END")
    return


def clientListener(conn, addr):
    global serverFlag
    clientConnected = True
    roomNumber = -1
    username = ""
    while serverFlag:
        try:
            data = conn.recv(1024)
            data = data.decode()
            if data:
                # 메세지 종류
                # ※x. x번째 채팅방에 입장(서버가 받음)
                # ※1. 새로운 유저 입장(클라가 받음)
                # ※2. 유저 나감(클라)
                # ※3. 유저 목록(클라)
                # ※0. 일반 메세지(클라)
                if data[0] == '※':
                    roomNumber = data[1]
                    username = data[2:]

                    client_list.append((conn, roomNumber, username))


                    # 방의 다른 유저들에게 유저가 들어옴을 알리기
                    printAndLog("client {} enter room{}".format(username, roomNumber))
                    message_to_send = "※1" + username
                    broadcast(message_to_send, conn, roomNumber)

                    # 처음 방에 들어온 유저에게는 이미 방에 있는사람 목록 보내주기
                    send_userList(conn, roomNumber)

                else:
                    message_to_send = "※0<" + username + "> " + data
                    broadcast(message_to_send, conn, roomNumber)
            else:
                clientLeave(conn, username, roomNumber)
                clientConnected=False
        except Exception as e:
            printAndLog(str(e))
            clientLeave(conn, username, roomNumber)
            clientConnected = False

        if not clientConnected:
            break


def broadcast(message, conn, room):
    message = message.encode()
    for client in client_list:
        if client[1] == room:
            try:
                client[0].send(message)
            except:
                client[0].close()
                remove(conn)

def send_userList(conn ,room):
    message ="※3"
    for client in client_list:
        if client[1] == room:
            message += client[2]
            message += "|"
    conn.send(message.encode())


def clientLeave(conn, username, roomNumber):
    printAndLog("client {} leave room{}".format(username, roomNumber))
    remove(conn)
    message_to_send = "※2" + username
    broadcast(message_to_send, conn, roomNumber)


def remove(conn):
    if conn in client_list:
        client_list.remove(conn)


def signal_handler(signal, frame):
    printAndLog("signal caught")
    global serverFlag
    serverFlag = False
    for client in client_list:
        client[0].close()


def main():
    signal.signal(signal.SIGINT, signal_handler)
    serverThread = threading.Thread(target=serverListener)
    serverThread.start()
    printAndLog("server is running. Ctrl+C for exit")
    while serverFlag:
        time.sleep(1)
#        print("hello")
#    serverThread.join()


if __name__ == '__main__':
    main()