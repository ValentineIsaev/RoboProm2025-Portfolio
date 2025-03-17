
import time


class Tasks:
    HALF_IMG = 250

    SLOW_SPEED = 10
    DEFAULT_SPEED = 25

    def __init__(self, f_c, b_c, move, s_m):
        self.switch = ''

        self.optimal_depth = 0
        self.optimal_yaw = 0
        self.speed = 0

        self.last_delta_x = 0
        self.areas = []

        self.checkpoint_data = {
            'image_data': 0,
            'depth_data': 0
        }

        self.front_eye = f_c
        self.bottom_eye = b_c
        self.move = move

        self.SIMULATOR_MODE = s_m

    def task1(self):
        if self.switch == 'search_first_square':
            self.move.rotate(self.optimal_yaw)
            area, delta_x, delta_y = self.front_eye.find_yellow_square()
            if area is None:
                # self.move.move_side(-100, 0)
                self.move.move_side(100, 0)
            else:
                self.switch = 'find_yellow_square'
        elif self.switch == 'find_yellow_square':
            self.move.rotate(self.optimal_yaw)
            area, delta_x, delta_y = self.front_eye.find_yellow_square()

            if area is not None:
                # self.move.move_side(-150, delta_y)
                self.move.move_side(150, delta_y)

                if len(self.areas) == 0:
                    self.areas.append(area)
                elif abs(self.last_delta_x - delta_x) > 30:
                    self.areas.append(area)

                self.last_delta_x = delta_x

                if len(self.areas) == 5:
                    print(self.areas)
                    self.switch = 'find_pink_circle'
                    # print(self.areas)
            else:
                self.move.move_side(100, 0)
        elif self.switch == 'find_pink_circle':
            self.__rotate(self.optimal_yaw)
            delta_x, delta_y, area = self.front_eye.find_pink_circle()
            if delta_x is not None:
                self.optimal_depth = self.move.get_depth() - delta_y * 0.002
                self.move.move_side(delta_x, delta_y)
                if abs(delta_x) < 15 and abs(delta_y) < 15:
                    if area > 90000:
                        self.move.move_side(0, 0)
                        res = 5 - self.areas.index(max(self.areas))
                        for i in range(res):
                            self.move.shoot()
                            time.sleep(1.5)
                        self.move.move_side(0, 0)
                        self.switch = 'rotate_on_line'
                        self.optimal_depth = 1.4
                        self.optimal_yaw = 0
                    else:
                        self.move.keep_yaw(self.move.get_yaw(), 10)
            else:
                self.move.move_side(-200, 0)
        elif self.switch == 'rotate_on_line':
            self.move.rotate(self.optimal_yaw)
            if abs(self.move.get_yaw()) < 5:
                self.move.rotate(self.move.get_yaw())
                self.switch = ''
                return 'TASK5'
        else:
            # self.switch = 'go_to_position'
            self.switch = 'search_first_square'
            self.optimal_depth = 1
            self.optimal_yaw = -90

        self.move.keep_depth(self.optimal_depth)

        return 'TASK1'

    def task2(self):

        if not self.switch:
            self.switch = 'TO_SCREWS'
        # print(f'SWITCH: {self.switch}')

        if self.switch == 'TO_SCREWS':
            boat_depth = self.move.get_depth()
            is_stop = self.front_eye.sum_mask(110*10**3, 'red')
            if is_stop:
                self.optimal_depth = boat_depth
                self.checkpoint_data['depth_data'] = boat_depth
                self.switch = 'LEFT_SCREW_STEP1'

                # print(f'FIRST DEPTH AND CHECKPOINTS DEPTH: {boat_depth}')
            else:
                self.move.move_side(8, boat_depth-100)

        elif self.switch.startswith('LEFT_SCREW'):
            self.__go_to_screw(mode="LEFT", new_switch='GO_TO_HOME')

        elif self.switch == 'GO_TO_HOME':
            num_cnt = 0
            nums_screw = {
                'HOME': 2,
                'SERVER': 1
            }
            num_screw = nums_screw.get(self.SIMULATOR_MODE)

            checkpoint_depth = self.checkpoint_data.get('depth_data')
            checkpoint_image_data = self.checkpoint_data.get('image_data')

            if checkpoint_image_data:
                # print('GET CHECKPOINT')
                if self.SIMULATOR_MODE == 'HOME':
                    is_distance = not self.front_eye.sum_mask(80*10**3, 'green')
                else:
                    is_distance = self.front_eye.is_distance_gray_screw(50*10**3)

                is_checkpoint = not self.front_eye.sum_mask(checkpoint_image_data, 'red', mode='[]')
            else:
                is_distance, is_checkpoint = True, True
                num_cnt = self.front_eye.search_points_screws(mode='LEN_CNT')

            if checkpoint_depth != 0 and self.optimal_depth != checkpoint_depth:
                self.optimal_depth = checkpoint_depth

            if is_checkpoint and is_distance:
                # STATE: CHECKPOINT
                # print('CHECKPOINT STATE')

                if checkpoint_image_data:
                    for key, value in zip(self.checkpoint_data.keys(), (0, 0)):
                        self.checkpoint_data[key] = value
                    self.speed = 0

                if num_cnt != num_screw:
                    # print('SIDEWAYS')
                    state_motors = 'SIDEWAYS'
                else:
                    # print('STOP')
                    state_motors = 'POWER_OFF'
            else:
                # STATE: DISTANCE
                # print('DISTANCE')

                state_motors = 'BACKWARDS'

            if state_motors == 'BACKWARDS' or not self.speed:
                # print('GO_BACK')
                self.move.keep_yaw(0, -self.speed)
                self.speed = self.DEFAULT_SPEED
            elif state_motors == 'SIDEWAYS':
                # print('GO_SIDEWAYS')
                self.move.move_side(-100, 0)
            else:
                # print('END GO TO HOME')
                self.speed = 0
                self.switch = 'RIGHT_SCREW_STEP1'

        elif self.switch.startswith('RIGHT_SCREW'):
            self.__go_to_screw(mode='RIGHT', new_switch='END_TASK')

        elif self.switch == 'END_TASK':
            x, y, shape = self.bottom_eye.detect_line()

            if y is not None and y - shape[1] < 5 and y > 0:
                self.speed = -5
            else:
                self.speed = 20

            self.move.move_forward_backward(-self.speed)
            if self.speed <= 0:
                self.__reset()
                return 'TASK4'

        self.__maintain_depth()

        self.__show_state()     # f'TIME: {time.time() - s_time:.2f}', (0, 400)

        return 'TASK2'

    def task3(self):
        if not self.switch:
            self.switch = 'ROTATE'
            self.optimal_depth = 1.9

        if self.switch == 'ROTATE':
            if self.__rotate(90):
                # self.__rotate(0)
                self.switch = 'SEARCH_DAMAGE'

        elif self.switch == 'SEARCH_DAMAGE':
            print('stop')
            # self.move.move_side(-90, 0)

        self.__maintain_depth()

        self.__show_state()

        return 'TASK3'

    def task4(self):
        if self.switch == 'FRONT_ARROW':
            delta_x, delta_y, delta_angle = self.front_eye.detect_arrow()

            if delta_x is not None:
                self.move.move_side(-delta_x, 0)
                self.move.keep_yaw(self.move.get_yaw() + delta_angle, 0)
            if abs(self.move.get_depth() - self.optimal_depth) < 0.05 \
             and abs(delta_angle) < 5 and abs(delta_x) < 5:
                self.optimal_depth = 3.15
                self.switch = 'GO_FORWARD'
            else:
                self.move.keep_yaw(self.move.get_yaw(), 0)
        elif self.switch == 'GO_FORWARD':
            self.move.keep_yaw(0, 40)
            line_x, line_y, shape = self.bottom_eye.detect_line()
            if line_y is not None and line_y < 140:
                self.optimal_depth = 1
                self.optimal_yaw = 90
                self.switch = 'ROTATE_ON_LINE'
        elif self.switch == 'ROTATE_ON_LINE':
            if self.__rotate(90, error=15):
                self.switch = 'MOVE_TO_TURN'
        elif self.switch == 'MOVE_TO_TURN':
            self.__follow_line()
            if abs(abs(self.move.get_yaw()) - 180) < 15:
                self.optimal_yaw = -90
                self.switch = 'ROTATE_ON_SHIP'
        elif self.switch == 'ROTATE_ON_SHIP':
            if abs(self.move.get_yaw()) > 160: 
                self.move.set_motor(0, 50)
                self.move.set_motor(1, -50)
            elif -160 < self.move.get_yaw() < -90:
                self.move.set_motor(0, 30)
                self.move.set_motor(1, -30)
            else:
                error = self.move.get_yaw() + 90
                self.move.keep_yaw(self.move.get_yaw() + error * 1.4, 0)
                if abs(error) < 5:
                    self.switch = ''
                    return 'TASK1'
        else:
            self.switch = 'FRONT_ARROW'
            self.optimal_depth = 3.3

        self.__maintain_depth()
        
        return 'TASK4'

    def task5(self):
        if self.switch == 'DETECT_CIRCLE':
            self.__follow_line()
            
            x, y = self.bottom_eye.detect_red_circle()
            if x is not None:
                self.switch = 'GO_TO_CIRCLE'
                self.optimal_depth = 2
        elif self.switch == 'GO_TO_CIRCLE':
            x, y = self.bottom_eye.detect_red_circle()

            if x is not None:
                delta_x, delta_y, delta_angle = self.\
                move.get_delta(x, y, (500, 500))

                # print(delta_angle, delta_y, delta_x)
                
                self.move.set_motor(4, delta_x * 0.3)
                self.move.set_motor(1, delta_y * 0.1)
                self.move.set_motor(0, delta_y * 0.1)

                if abs(delta_x) < 8 and abs(delta_y) < 8:
                    self.switch = 'GO_SURFACE'
        elif self.switch == 'GO_SURFACE':
            self.optimal_depth = -100

            if self.move.get_depth() < 0:
                exit()
        else:
            self.switch = 'DETECT_CIRCLE'
            self.optimal_depth = 1.5

        self.__maintain_depth()

        return 'TASK5'

    def __maintain_depth(self):
        if self.optimal_depth:
            self.move.keep_depth(self.optimal_depth)

    def __follow_line(self):
        line_x, line_y, img_shape = self.bottom_eye.detect_line()
        if line_x is not None:
            _, delta_y, delta_angle = self.move.get_delta(line_x, line_y, img_shape)
            self.move.follow_line(delta_y, delta_angle*1.5)

        return line_x, line_y

    def __show_state(self, *args):

        if self.SIMULATOR_MODE == 'HOME':
            self.front_eye.text_on_frame(
                'SPEED: '+str(self.speed), (0, 30),
                'DEPTH: '+str(round(self.optimal_depth, 1)), (0, 70),
                'STEP: '+self.switch, (0, 110), *args)

            self.front_eye.show_image('BIN', show_thresh=True)
            self.front_eye.show_image('MAIN')

    def __go_to_screw(self, mode, new_switch: str):
        if self.switch.endswith('STEP1'):
            # print('STEP1')

            screw_data = self.front_eye.search_points_screws(mode=mode)
            if screw_data:
                self.__screw_step1(screw_data)

        elif self.switch.endswith('STEP2'):
            masks = {
                'HOME': 'green',
                'SERVER': 'gray'
            }
            is_screw_in_frame = self.front_eye.sum_mask(10 * 10 ** 3, masks.get(self.SIMULATOR_MODE))

            if self.speed != self.DEFAULT_SPEED:
                self.speed = self.DEFAULT_SPEED

            if is_screw_in_frame:
                # # print('END STEP2')
                self.speed = 0
                self.switch = new_switch

            self.move.keep_yaw(0, -self.speed)

    def __screw_step1(self, screw_data):
        x, y, state = screw_data

        opposite_screw = self.move.sideways_movement(x, y, self.HALF_IMG)
        if opposite_screw:
            if not self.checkpoint_data.get('image_data'):
                self.checkpoint_data['image_data'] = self.front_eye.mask_and_sum('red')
                # print(f'SAVE CHECKPOINT: {self.checkpoint_data["image_data"]}')

            if state == 'SLOWING' and self.speed > self.SLOW_SPEED:
                self.speed = self.SLOW_SPEED
            if state != 'STOP':
                if not self.speed:
                    self.speed = self.DEFAULT_SPEED
            else:
                self.switch = self.switch[:-5] + 'STEP2'
                self.speed = 1

                self.front_eye.search_on = True
                self.move.is_at_target = False

        if self.speed:
            self.optimal_depth = self.move.go_to_point(x, y, self.HALF_IMG, speed=self.speed)

    def __rotate(self, angle, error=9):
        if not self.optimal_yaw:
            self.optimal_yaw = angle + self.move.get_yaw()
        state = self.move.rotate(self.optimal_yaw, error)
        if state:
            self.optimal_yaw = 0

        return state

    def __reset(self):
        self.speed = self.DEFAULT_SPEED
        self.switch = ''
