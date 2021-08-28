import socket
import asyncio
import uuid
import json
from datetime import datetime


class Log:
    messages = None
    filename = None

    def __init__(self, filename):
        self.filename = filename
        self.messages = []

    def log(self, message):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.messages.append(now + ': ' + message)

    def cleanmessages(self):
        self.messages = []

    def write(self):
        if self.messages is not None and len(self.messages) > 0:
            with open(self.filename, 'a') as file:
                for text in self.messages:
                    file.write(text + '\n')
            self.cleanmessages()


class Server:
    socket = None
    main_loop = None
    log = None

    def __init__(self, logfile=None):
        self.socket = []
        self.socket.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        self.socket[-1].bind(('', 8000))
        self.socket.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        self.socket[-1].bind(('', 8001))
        for s in self.socket:
            s.listen(50)
            s.setblocking(False)
        self.main_loop = asyncio.new_event_loop()
        self.user_keys = {}
        if logfile is not None:
            self.log = Log(logfile)

    def canceltasks(self):
        for task in asyncio.Task.all_tasks():
            task.cancel()

    def __del__(self):
        if self.socket is not None and len(self.socket) > 0:
            for s in self.socket:
                s.close()
            self.socket = None

    async def accept(self, sock):
        while True:
            print('Wait connection on port ' + str(sock.getsockname()[1]))
            user_socket, user_addr = await self.main_loop.sock_accept(sock)
            print(f'Connect user {user_socket}')
            self.main_loop.create_task(self.listen(user_socket))

    async def listen(self, user_socket=None):
        if user_socket is None:
            return

        data = await self.main_loop.sock_recv(user_socket, 1024)

        if user_socket.getsockname()[1] == 8000:
            name = data.decode('utf-8')
            if name in self.user_keys:
                self.main_loop.create_task(
                    self.sendmessage(user_socket,
                                     self.genmessage('Идентификатор уже занят', True)))
            else:
                self.user_keys[name] = self.gencode(name)
                self.main_loop.create_task(
                    self.sendmessage(user_socket, self.genmessage(self.user_keys[name])))
        elif user_socket.getsockname()[1] == 8001:
            data = json.loads(data.decode('utf-8'))
            if data['name'] in self.user_keys and data['code'] == self.user_keys[data['name']]:
                self.log.log(f"Got message \'{data['message']}\' from {data['name']}")
                self.log.write()
                del self.user_keys[data['name']]
                self.main_loop.create_task(
                    self.sendmessage(user_socket, self.genmessage('Сообщение получено')))
            else:
                self.main_loop.create_task(
                    self.sendmessage(user_socket, self.genmessage('Код не совпадает', True)))

    async def sendmessage(self, user_socket=None, message=None):
        if user_socket is None or message is None:
            return

        await self.main_loop.sock_sendall(user_socket, message.encode('utf-8'))

    async def main(self):
        await asyncio.gather(
            self.main_loop.create_task(self.accept(self.socket[0])),
            self.main_loop.create_task(self.accept(self.socket[1])),
            self.main_loop.create_task(self.controls())
        )

    async def controls(self):
        while True:
            command = await self.main_loop.run_in_executor(None, input)
            if command in ('quit', 'q'):
                self.canceltasks()
                break

    def gencode(self, name):
        return str(uuid.uuid5(uuid.NAMESPACE_X500, name))

    def start(self):
        print('Сервер запущен, для выхода наберите quit')
        try:
            self.main_loop.run_until_complete(self.main())
        except asyncio.CancelledError:
            print('Выход')
            self.main_loop.close()
            self.main_loop = None

    def genmessage(self, message, error=False):
        return json.dumps({'error': error, 'message': message})


if __name__ == '__main__':
    server = Server('logfile.log')
    server.start()
