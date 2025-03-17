import json
import time
import os

import numpy as np
import cv2

from mcx import MCX


class Step:
    def __init__(self, name: str, is_graper: bool = False, angle: int = 0):
        self.name = name
        self.is_graper = is_graper
        self.angle = angle

    def __str__(self):
        return self.name


class Steps:
    def __init__(self, steps):
        self.__steps = steps
        self._index = 0

    @property
    def step(self):
        return self.__steps[self._index]

    def next_step(self):
        if len(self.__steps) - 1 > self._index:
            self._index += 1

    @property
    def is_stop(self):
        return True if self._index == len(self.__steps) - 1 else False


ROBOT_NAME = "Robot9_1"

GO_TO_FLASK_STEPS = (
    Step("GO_TO_FLASK"),
    Step("DESCENT_GO_TO_FLASK"),
    Step("CAPTURE_FLASK"),
    Step("UPPER_Z", True),
)

GO_TO_CAMERA_STEPS = (
    Step("GO_TO_CAMERA"),
    Step("DESCENT_TO_CAMERA"),
)

EXIT_FLASK = (
    Step("UPPER_Z", True),
    Step("GO_TO_FLASK", True),
    Step("DESCENT_GO_TO_FLASK", True),
    Step("RELEASE_FLASK"),
    Step("GO_TO_START")
)

STEPS_FIRST = (
    *GO_TO_FLASK_STEPS,
    *GO_TO_CAMERA_STEPS,
    *EXIT_FLASK
)

STEPS_SECOND = (
    *GO_TO_FLASK_STEPS,
    *GO_TO_CAMERA_STEPS,
    Step("ROTATE_FLASK", angle=45),
    *EXIT_FLASK
)

STEPS_THIRD = (
    *GO_TO_FLASK_STEPS,
    *GO_TO_CAMERA_STEPS,
    Step("RECEIVE_FLASK"),
    *EXIT_FLASK
)

Z_FLASK = 95
COUNT_IMAGES = 8
NUMBER_VIDEOS = 1
VIDEO_SIZE = (500, 500)

# -------------------------
ROTATE_SLEEP = 0.5
IS_CHECK_SEND = False
IS_NONE_ROTATE_SLEEP = False
# -------------------------


def get_image(manipulate: MCX):
    image_byte = manipulate.getCamera1Image()
    if image_byte:
        image_np = np.frombuffer(image_byte, np.uint8)
        image_np = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
        return image_np
    return None


def save_manipulator_image(file_name, manipulate: MCX):
    with open(file_name, 'w') as file:
        file.write(manipulate.getCamera1Image())


def create_video(frames):
    global NUMBER_VIDEOS

    writer = cv2.VideoWriter(f"Video_{NUMBER_VIDEOS}.avi", cv2.VideoWriter_fourcc(*'XVID'), 15, VIDEO_SIZE)

    for frame in frames:
        frame = cv2.resize(frame, VIDEO_SIZE)
        writer.write(frame)

    writer.release()


def json_load(file_name):
    with open(file_name, 'r') as json_file:
        data_from_file = json.load(json_file)
    return data_from_file


# Tree variant of function
def manipulate_move(manipulate, x, y, z, t, grapper):
    manipulate.move(ROBOT_NAME, x, y, z, t, grapper)
    if IS_CHECK_SEND:
        while manipulate.getManipulatorStatus() == 0:
            time.sleep(0.2)


def flask_move(manipulate: MCX, steps: Steps, start_coordinates: list, camera_coordinates: list, point_coordinates):
    start_x, start_y, start_z = start_coordinates
    camera_x, camera_y, camera_z = camera_coordinates
    x, y, z = point_coordinates

    step = steps.step
    if manipulate.getManipulatorStatus() == 0:
        manipulate_x, manipulate_y, manipulate_z, rotate_x, rotate_y, rotate_z = manipulate.getManipulatorMotor()
        print(f"Step: {step}")
        match step.name:
            case ("GO_TO_FLASK"):
                manipulate_move(manipulate, x, y, manipulate_z, 0, int(step.is_graper))
            case ("DESCENT_GO_TO_FLASK"):
                manipulate_move(manipulate, manipulate_x, manipulate_y, Z_FLASK, 0, int(step.is_graper))
            case ("CAPTURE_FLASK"):
                manipulate_move(manipulate, manipulate_x, manipulate_y, z, 0, 1)
            case ("UPPER_Z"):
                manipulate_move(manipulate, manipulate_x, manipulate_y, start_z, 0, int(step.is_graper))
            case ("GO_TO_CAMERA"):
                manipulate_move(manipulate, camera_x, camera_y, start_z, 0, 1)
            case ("DESCENT_TO_CAMERA"):
                manipulate_move(manipulate, manipulate_x, manipulate_y, camera_z, 0, 1)
            case ("REALESE_FLASK"):
                manipulate_move(manipulate, manipulate_x, manipulate_y, manipulate_z, 0, 0)
            case "GO_TO_START":
                manipulate_move(manipulate, start_x, start_y, start_z, 0, 0)

            case "ROTATE_FLASK":
                count_image = 0
                angles_rotate = list(range(0, 225, 45)) + list(range(-135, 1, 45))

                while count_image <= COUNT_IMAGES - 1:
                    if manipulate.getManipulatorStatus() == 0:
                        cv2.imread(f"FRAME_{count_image}.png", get_image(manipulate))
                        count_image += 1
                        manipulate_move(manipulate, manipulate_x, manipulate_y, manipulate_z,
                                        angles_rotate[count_image], 1)
                    time.sleep(0.01)

            case "RECEIVE_FLASK":
                angles = list(range(1, 180, 10)) + list(range(-180, 1, 10))
                number_image = 0
                frames = []
                while number_image <= len(angles) - 1:
                    if manipulate.getManipulatorStatus() == 0:
                        manipulate_move(manipulate, manipulate_x, manipulate_y, manipulate_z, angles[number_image], 1)
                        print("ROTATE GRAPPERRRRRR!")
                        image = get_image(manipulate)
                        frames.append(image)
                        number_image += 1

                        time.sleep(ROTATE_SLEEP)

                    if IS_NONE_ROTATE_SLEEP:
                        time.sleep(0.01)

                create_video(frames)

        steps.next_step()
        time.sleep(0.5)


def load_point() -> str:
    point = input()
    return point


def load_points() -> list[str]:
    return input().split()


STEPS = {
    1: Steps(STEPS_FIRST),
    2: Steps(STEPS_SECOND),
    3: Steps(STEPS_THIRD)
}


def main(task: int, manipulate: MCX):
    points = load_points()
    coordinates = json_load("coordinates.json")

    for point in points:
        if point not in coordinates.keys():
            raise ValueError("Input wrong key-point")
        steps = STEPS.get(task)

        while True:
            flask_move(manipulate, steps, coordinates.get('start'),
                       coordinates.get('camera'),
                       (*coordinates.get(point), 95))

            if manipulate.getManipulatorWarning() != 0:
                print(manipulate.getManipulatorWarningStr())

            if steps.is_stop:
                break

            time.sleep(0.01)


if __name__ == "__main__":
    my_robot = MCX()
    time.sleep(1)
    main(3, my_robot)