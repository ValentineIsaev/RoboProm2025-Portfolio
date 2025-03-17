import socket
import math

import cv2


def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('172.16.65.51', 12345)) # 127.16.65.51

    message = 'get coordinates'
    client_socket.sendall(message.encode())
    coordinates = ''
    while True:
        data = client_socket.recv(1024).decode()
        print('got data')
        if data.startswith('Coordinates'):
            coordinates = data
            client_socket.sendall('eho'.encode())
        elif data == 'done':
            client_socket.sendall(coordinates.encode())
            break
    client_socket.close()


if __name__ == '__main__':
    main()