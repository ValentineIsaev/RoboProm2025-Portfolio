import socket

import cv2
import random

EXAMPLE_COORDINATES = (
    (2.302, 2.791),
    (2.582, 5.096),
    (0.968, 1.241),
    (2.673, 0.417),
    (2.023, 3.848),
    (1.638, 4.786),
    (0.193, 1.722)
)


def generate_coordinates(n: int) -> str:
    points = ""
    coordinates = random.sample(EXAMPLE_COORDINATES, n)
    for number, coordinate in zip(range(1, n+1, 1), coordinates):
        points += f'{number}|{coordinate[0]},{coordinate[1]}|0;'

    return 'Coordinates:' + points


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('172.16.65.51 ', 12345))
    server.listen(1)
    print('Server start!')

    while True:
        client_socket, addr = server.accept()
        print(f"Подключено к {addr}")

        is_input = False
        while True:
            data = client_socket.recv(1024).decode()
            if data == 'get coordinates':
                print('Send coordinates')
                client_socket.sendall(generate_coordinates(4).encode())
            elif data.startswith('eho'):
                client_socket.sendall('done'.encode())
            elif data.startswith('Coordinates'):
                make_map(data.replace('Coordinates', ''))

        client_socket.close()


LEN_X = 3.04
LEN_Y = 5.4


def make_map(coordinates: str):
    my_map = cv2.imread('map.png')

    for data in coordinates.split(';'):
        number_point, coordinates, passes = data.split('|')
        x, y = map(float, coordinates.split(','))
        print(f'point_coordinate: {x, y}')

        map_x, map_y = round((my_map.shape[1] / LEN_X) * x), my_map.shape[0] - round((my_map.shape[0] / LEN_Y) * y)
        cv2.circle(my_map, (map_x, map_y), 10, (0, 0, 255), -1)

        cv2.putText(my_map, number_point, (map_x - 30, map_y + 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(my_map, passes, (map_x - 30, map_y + 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    cv2.imshow('MAP', my_map)
    cv2.waitKey(0)


if __name__== '__main__':
    main()