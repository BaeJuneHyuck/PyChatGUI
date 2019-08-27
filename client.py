import tkinter
from tkinter import scrolledtext
import socket
import threading


class ChatList():
    root = None
    list = None
    btn = None
    nameBox = None
    label = None

    roomOpened = False
    selectedRoom = 0
    host = ''
    port = 0

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.setUI()

    def setUI(self):
        self.root = tkinter.Tk()
        self.root.title('py Chat')
        self.root.resizable(False, False)
        self.root.grid_columnconfigure(3)
        self.root.grid_rowconfigure(2)

        self.list = tkinter.Listbox(self.root, height=10, width=60)
        for i in range(10):
            #self.list.insert(i, "room {} : {}/100".format(i, self.member[i]))
            self.list.insert(i, "room {}".format(i))

        self.list.bind('<<ListboxSelect>>', self.listSelect)
        self.list.grid(row=0, column=0, columnspan=3)
        self.list.selection_set(0)
        self.list.focus_set()

        self.label = tkinter.Label(self.root, text="input your name")
        self.label.grid(row=1, column=0)

        self.nameBox = tkinter.Entry(self.root, text="Input Name")
        self.nameBox.grid(row=1, column=1)

        self.btn = tkinter.Button(self.root, text="Enter room", command= lambda:{
            self.enterRoom(self.root)
        })
        self.btn.grid(row=1, column=2)
        self.root.bind("<Return>", self.enterRoom)

        self.root.mainloop()

    def listSelect(self, event):
        if self.roomOpened:
            return
        w = event.widget
        length = w.curselection()
        if length:
            self.selectedRoom = int(w.curselection()[0])
#        index = int(w.curselection()[0])
#        value = w.get(index)
#        print('You selected item %d: "%s"' % (index, value))

    def enterRoom(self, event):
        name = self.nameBox.get()
        if name == '':
            self.label.config(text="Name is empty!", fg="#FF0000")
            return
        if "|" in name:
            self.label.config(text="'|' Is not allowed", fg="#FF0000")
            return
        if self.roomOpened:
            return
        self.roomOpened = True
        self.root.withdraw()
        room = ChatWindow(self.host, self.port, self.root, self.selectedRoom, name)


class ChatWindow():
    root = None
    text = None
    input = None
    users = None
    roomNumber = -1
    rootListWindow = None
    name = None
    userList = []

    server = None
    serverThread = None
    threadFlag = True


    def __init__(self,host, port, root, number, name):
        self.rootListWindow = root
        self.HOST = host
        self.PORT = port
        self.roomNumber = number
        self.name = name
        self.setUI()

    def setUI(self):
        self.root = tkinter.Tk()
        self.root.title('py Chat : room {}'.format(self.roomNumber))
#        self.root.geometry('{}x{}'.format(650, 220))
        self.root.resizable(False,False)
        self.root.grid_columnconfigure(2)
        self.root.grid_rowconfigure(2)

        self.text = scrolledtext.ScrolledText(self.root, height=15, width=60)
        self.text.grid(row=0, column=0)
        self.text.config(state=tkinter.DISABLED)
        self.text.tag_config('system', background="white", foreground="red")

        self.users = scrolledtext.ScrolledText(self.root, height=15, width=20)
        self.users.grid(row=0, column=1, rowspan= 2)
        self.users.config(state=tkinter.DISABLED)

        self.input = tkinter.Entry(self.root, width=60)
        self.input.grid(row=1, column=0)
        self.input.bind("<Return>", self.send_message)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.input.focus_set()
        self.root.focus_force()
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.connect((self.HOST, self.PORT))
            self.serverThread = threading.Thread(target=self.listener, args=(self.server,)).start()
        except:
            print("connect fail...")
            self.on_closing()

        self.root.mainloop()

    def send_message(self, event):
        message = self.input.get() + '\n'
        if message == "":
            return
        if message[0] == '※':
            self.print_message("  [system] 문장은 '※'로 시작할 수 없습니다!", True)
            return
        self.input.delete(0,"end")
        try:
            self.server.send(message.encode())
        except:
            print("서버와의 연결이 끊어졋습니다")
            self.on_closing()

    def listener(self, server):
        # 처음 서버와 연결시 본인이 몇번째 방에 들어가는지 알려줌
        message = "※"+str(self.roomNumber)+self.name
        self.server.send(message.encode())

        serverFail = False
        while self.threadFlag:
            try:
                message = server.recv(2048)
                if message:
                    # 메세지 종류
                    # ※xUser. x(0~9)번째 채팅방에 User가 입장(서버가 받음)
                    # ※1. 새로운 유저 입장(클라가 받음)
                    # ※2. 유저 나감(클라)
                    # ※3. 유저리스트 전송받음
                    # ※0. 일반 메세지(클라)
                    message = message.decode()
                    print("message : ",message)
                    if message[0] == '※':
                        if message[1] == '1':
                            name = message[2:]
                            self.add_userlist(name)
                            self.print_message("  {} entered room\n".format(name), True)
                        elif message[1] == '2':
                            name = message[2:]
                            self.del_userlist(name)
                            self.print_message("  {} left room\n".format(name), True)
                        elif message[1] == '3':
                            name = message[2:]
                            self.update_userlist(name)
                        elif message[1] == '0':
                            self.print_message(message, False)
                else:
                    print("client leave")
                    server.close()
                    serverFail = True
            except:
                continue
            if serverFail:
                server.close()
                break

    def add_userlist(self, name):
        self.userList.append(name)
        self.print_userList()

    def del_userlist(self, name):
        for user in self.userList:
            if user == name:
                self.userList.remove(user)
        self.print_userList()

    def update_userlist(self, message):
        print("user list updated")
        newlist = message.split("|")
        print("new list :" ,newlist)
        self.userList = newlist
        self.print_userList()

    def print_userList(self):
        self.users.config(state=tkinter.NORMAL)
        self.users.delete('1.0', tkinter.END)
        self.users.update()
        for user in self.userList:
            if user != "":
                self.users.insert('end', user+"\n")
        self.users.config(state=tkinter.DISABLED)

    def on_closing(self):
        print("good bye")
        self.threadFlag = False
        self.server.close()
        self.root.quit()
        self.root.destroy()
        self.rootListWindow.quit()
        self.rootListWindow.destroy()

    def print_message(self, message, system):
        self.text.config(state=tkinter.NORMAL)
        if system:
            self.text.insert('end', message[2:], 'system')
        else:
            self.text.insert('end', message[2:])
        self.text.config(state=tkinter.DISABLED)

def main():
    SERVER = '127.0.0.1'
    SERVER_PORT = 3118
    room = ChatList(SERVER, SERVER_PORT)


if __name__ == "__main__":
    main()