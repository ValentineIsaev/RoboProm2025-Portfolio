
import os

import cv2


def main():
    for file in os.listdir():
        if file.endswith('avi'):
            cap = cv2.VideoCapture(file)

            if not cap.isOpened():
                print('error')

            while True:
                status, frame = cap.read()
                print(status)
                if not status:
                    print('none')
                    break

                cv2.imshow("FRAME", frame)
                cv2.waitKey(0)


if __name__ == '__main__':
    main()
