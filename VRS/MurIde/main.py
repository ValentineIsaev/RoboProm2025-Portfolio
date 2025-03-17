import time

import pymurapi as mur

import time
from tasks import Tasks
from eyes import vision
from moving import Move

auv = mur.mur_init()
simulator_mode = 'HOME'     # HOME or SERVER
SLEEP = 0.02

front_eye, bottom_eye = vision
move = Move(auv)
tasks = Tasks(front_eye, bottom_eye, move, simulator_mode)


def main():
    start_time = time.monotonic()

    state = 'TASK2'
    tasks_function = {
        'TASK1': tasks.task1,
        'TASK2': tasks.task2,
        'TASK3': tasks.task3,
        'TASK4': tasks.task4,
        'TASK5': tasks.task5
    }

    sleep_data = {
        'HOME': 0,
        'SERVER': 0.015
    }
    sleep = sleep_data.get(simulator_mode)

    while state != 'END':
        front_eye.add_new_frame(auv.get_image_front())
        bottom_eye.add_new_frame(auv.get_image_bottom())

        state = tasks_function.get(state)()

        if simulator_mode == 'HOME':
            front_eye.show_time(round(time.monotonic() - start_time, 1))

        time.sleep(SLEEP)


if __name__ == '__main__':
    main()
    