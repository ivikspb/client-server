import socket
import json


class Client:
    socket = None
    name = None
    code = None

    def __init__(self, name):
        self.name = name

    def __del__(self):
        if self.socket is not None:
            self.socket.close()
            self.socket = None

    def connection(self, ip, port):
        try:
            self.socket = socket.create_connection((ip, port))
        except ConnectionRefusedError:
            print('Сервер недоступен')
            exit(0)

    def waitresponse(self):
        if self.socket is not None:
            data = self.socket.recv(1024)
            data = json.loads(data.decode('utf-8'))
            return data
        else:
            return None

    def getcode(self):
        self.connection('127.0.0.1', 8000)
        self.socket.send(self.name.encode('utf-8'))
        data = self.waitresponse()
        if data is None:
            print('Ответ от сервера не получен')
            return False
        if data['error'] is False:
            self.code = data['message']
            print('Get code '+self.code)
            self.socket.close()
            self.socket = None
            return True
        else:
            print(data['message'])
            return False

    def sendmessage(self, message=None):
        if message is None or message == '':
            return

        data = {'message': message, 'code': self.code, 'name': self.name}
        self.connection('127.0.0.1', 8001)
        self.socket.send(json.dumps(data).encode('utf-8'))
        data = self.waitresponse()
        if data is not None:
            print(data['message'])
        self.socket.close()
        self.socket = None


if __name__ == '__main__':
    code_received = False
    client = None
    while not code_received:
        name = input('Введите свой идентификатор: ')
        if name != '':
            client = Client(name)
            code_received = client.getcode()

    # Для проверки вывода ошибки при передачи неверного кода
    # client.code = client.code[::-1]
    message = input('Введите сообщение для отправки: ')
    client.sendmessage(message)
