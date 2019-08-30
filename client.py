import tkinter
from tkinter import scrolledtext
import socket
import threading


class WelcomeWindow:
    root = None
    address_box = None
    port_box = None
    name_box = None
    btn = None
    label = None
    label_set = False

    server = None

    def __init__(self):
        self._set_ui()

    def _set_ui(self):
        self.root = tkinter.Tk()
        self.root.title('py Chat')
        self.root.resizable(False, False)
        self.root.grid_columnconfigure(3)
        self.root.grid_rowconfigure(5)

        label = tkinter.Label(self.root, text="Host Address")
        label.grid(row=0, column=0)

        self.address_box = tkinter.Entry(self.root)
        self.address_box.insert(tkinter.END, "127.0.0.1")
        self.address_box.grid(row=0, column=1, columnspan=2)

        label2 = tkinter.Label(self.root, text="Port")
        label2.grid(row=1, column=0)

        self.port_box = tkinter.Entry(self.root)
        self.port_box.insert(tkinter.END, "3118")
        self.port_box.grid(row=1, column=1, columnspan=2)

        label3 = tkinter.Label(self.root, text="Name")
        label3.grid(row=2, column=0)

        self.name_box = tkinter.Entry(self.root)
        self.name_box.grid(row=2, column=1, columnspan=2)
        self.name_box.focus_set()

        self.btn = tkinter.Button(self.root, text="Enter", command=lambda: {
            self._enter_server()
        })
        self.btn.grid(row=3, column=1)
        self.root.bind("<Return>", self._enter_server)

        self.label = tkinter.Label(self.root, bg="#FFF", fg="#FFF")

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.root.mainloop()

    def _enter_server(self, event=None):
        name = self.name_box.get()
        if name == '':
            if not self.label_set:
                self.label_set = True
                self.label.grid(row=4, column=0, columnspan=3)
            self.label.config(text="Name is empty!", fg="#FF0000")
            return
        if "|" in name:
            if not self.label_set:
                self.label_set = True
                self.label.grid(row=4, column=0, columnspan=3)
            self.label.config(text="'|' Is not allowed", fg="#FF0000")
            return

        host = self.address_box.get()
        port = int(self.port_box.get())
        print(host, port, name)

        try:
            self.server.connect((host, port))
            self.server.settimeout(1)
            message = "※※"+name
            self.server.send(message.encode())
            print("대기실 소켓:", self.server)

            # while True:
            user_list_message = self.server.recv(1024)
            print(user_list_message.decode())
#            self.root.quit()
#            self.root.destroy()

            self.root.withdraw()
            list_window = ChatList(self.server, name, user_list_message)
        except socket.error:
            if not self.label_set:
                self.label_set = True
                self.label.grid(row=4, column=0, columnspan=3)
            self.label.config(text="server connection fail", fg="#FF0000")

    def _on_closing(self):
        self.server.close()
        self.root.quit()
        self.root.destroy()


class ChatList:
    root = None
    room_list_box = None
    user_list_box = None
    btn = None

    roomOpened = False
    selected_room = 0
    host = ''
    port = 0
    name = ''

    user_list = [[]]
    user_number = [0 for i in range(10)]
    server = None

    def __init__(self, server, name, message):
        self.server = server
        self.name = name
        self._decode_list(message)
        self._set_ui()

    def _decode_list(self, message):
        message = message.decode()
        message = message[1:]
        self.user_list = message.split("※")
        for room in range(10):
            self.user_list[room] = self.user_list[room][1:]
            self.user_list[room] = self.user_list[room].split("|")
            self.user_number[room] = len(self.user_list[room]) - 1

    def _set_ui(self):
        self.root = tkinter.Tk()
        self.root.title('py Chat')
        self.root.resizable(False, False)
        self.root.grid_columnconfigure(2)
        self.root.grid_rowconfigure(2)

        self.room_list_box = tkinter.Listbox(self.root, height=10, width=30)
        for i in range(10):
            room_text = "[ room {} ]  current user : {}".format(i, self.user_number[i])
            self.room_list_box.insert(i, room_text)

        self.user_list_box = scrolledtext.ScrolledText(self.root, height=12, width=30)
        self.user_list_box.grid(row=0, column=1)
        self.user_list_box.config(state=tkinter.DISABLED)

        self.room_list_box.bind('<<ListboxSelect>>', self._select_list)
        self.room_list_box.grid(row=0, column=0)
        self.room_list_box.selection_set(0)
        self.room_list_box.focus_set()

        name_label = tkinter.Label(self.root, text=self.name)
        name_label.grid(row=1, column=0)

        self.btn = tkinter.Button(self.root, text="Enter", command=lambda: {
            self._enter_room(self.root)
        })
        self.btn.config(borderwidth=2, relief="solid")
        self.btn.grid(row=1, column=1, sticky="we")
        self.root.bind("<Return>", self._enter_room)

        self._update_user_list_box()

        self.btn.focus_set()
        self.root.focus_force()
        self.root.mainloop()

    def _select_list(self, event):
        if self.roomOpened:
            return
        w = event.widget
        length = w.curselection()
        if length:
            self.selected_room = int(w.curselection()[0])

        self._update_user_list_box()

    def _update_user_list_box(self):
        self.user_list_box.config(state=tkinter.NORMAL)
        self.user_list_box.delete('1.0', tkinter.END)
        for user in self.user_list[self.selected_room]:
            if user != "":
                self.user_list_box.insert('end', user+"\n")
        self.user_list_box.config(state=tkinter.DISABLED)

    def _enter_room(self, event):
        if self.roomOpened:
            return
        self.roomOpened = True
        self.root.withdraw()
        room = ChatWindow(self.server, self.root, self.selected_room, self.name)


class ChatWindow:
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

    def __init__(self, server, root, number, name):
        self.rootListWindow = root
        self.server = server
        self.roomNumber = number
        self.name = name
        self._set_ui()

    def _set_ui(self):
        self.root = tkinter.Tk()
        self.root.title('py Chat : room {}'.format(self.roomNumber))
        self.root.resizable(False, False)
        self.root.grid_columnconfigure(2)
        self.root.grid_rowconfigure(2)

        self.text = scrolledtext.ScrolledText(self.root, height=15, width=60)
        self.text.grid(row=0, column=0)
        self.text.config(state=tkinter.DISABLED)
        self.text.tag_config('system', background="white", foreground="red")

        self.users = scrolledtext.ScrolledText(self.root, height=15, width=20)
        self.users.grid(row=0, column=1, rowspan=2)
        self.users.config(state=tkinter.DISABLED)

        self.input = tkinter.Entry(self.root, width=60)
        self.input.grid(row=1, column=0)
        self.input.bind("<Return>", self._send_message)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.input.focus_set()
        self.root.focus_force()
        self.serverThread = threading.Thread(target=self._server_listener, args=(self.server,)).start()
        self.root.mainloop()

    def _send_message(self, event):
        message = self.input.get() + '\n'
        if message == "":
            return
        if message[0] == '※':
            self._print_message("  [system] 문장은 '※'로 시작할 수 없습니다!", True)
            return
        self.input.delete(0, "end")
        try:
            self.server.send(message.encode())
        except socket.error:
            print("서버와의 연결이 끊어졋습니다")
            self._on_closing()

    def _server_listener(self, server):
        # 처음 서버와 연결시 본인이 몇번째 방에 들어가는지 알려줌
        message = "※"+str(self.roomNumber)
        self.server.send(message.encode())

        server_fail = False
        while self.threadFlag:
            try:
                message = server.recv(2048)
                if message:
                    # 메세지 종류
                    # ※※name 서버에 처음 접속요청 (서버가 받음)
                    # ※x x(0~9)번째 채팅방에 입장(서버가 받음)
                    # ※1 새로운 유저 입장(클라가 받음)
                    # ※2 유저 나감(클라)
                    # ※3 유저리스트 전송받음(클라)
                    # ※0 일반 메세지(클라)
                    message = message.decode()
                    print("message : ", message)
                    if message[0] == '※':
                        if message[1] == '1':
                            name = message[2:]
                            self._add_userlist(name)
                            self._print_message("  {} entered room\n".format(name), True)
                        elif message[1] == '2':
                            name = message[2:]
                            self._del_userlist(name)
                            self._print_message("  {} left room\n".format(name), True)
                        elif message[1] == '3':
                            name = message[2:]
                            self._update_userlist(name)
                        elif message[1] == '0':
                            self._print_message(message, False)
                else:
                    print("client leave")
                    server.close()
                    server_fail = True
            except socket.error:
                continue
            if server_fail:
                server.close()
                break

    def _add_userlist(self, name):
        self.userList.append(name)
        self._print_userlist()

    def _del_userlist(self, name):
        for user in self.userList:
            if user == name:
                self.userList.remove(user)
        self._print_userlist()

    def _update_userlist(self, message):
        print("user list updated")
        newlist = message.split("|")
        print("new list :", newlist)
        self.userList = newlist
        self._print_userlist()

    def _print_userlist(self):
        self.users.config(state=tkinter.NORMAL)
        self.users.delete('1.0', tkinter.END)
        self.users.update()
        for user in self.userList:
            if user != "":
                self.users.insert('end', user+"\n")
        self.users.config(state=tkinter.DISABLED)

    def _on_closing(self):
        print("good bye")
        self.threadFlag = False
        self.server.close()
        self.root.quit()
        self.root.destroy()
        self.rootListWindow.quit()
        self.rootListWindow.destroy()

    def _print_message(self, message, system):
        self.text.config(state=tkinter.NORMAL)
        if system:
            self.text.insert('end', message[2:], 'system')
        else:
            self.text.insert('end', message[2:])
        self.text.config(state=tkinter.DISABLED)


def main():
    WelcomeWindow()


if __name__ == "__main__":
    main()
