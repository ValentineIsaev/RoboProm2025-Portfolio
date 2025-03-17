from math import pi, atan2
import time


class PDRegulator:
    def __init__(self, p_gain, d_gain):
        self._p_gain = p_gain
        self._d_gain = d_gain

        self._prev_error = 0.0
        self._timestamp = 0

    def process(self, error):
        # Функция для вычисления выходного значения регулятора, оно будет использоваться моторами 

        timestamp = int(round(time.time() * 1000))
        if timestamp == self._timestamp:
            return 0

        output = self._p_gain * error + self._d_gain / (timestamp - self._timestamp) * (error - self._prev_error)

        self._timestamp = timestamp
        self._prev_error = error

        return output


class Move:
    SLEEP = 0    # 0.001

    def __init__(self, auv):
        self.auv = auv

        self.yaw_regulator = PDRegulator(0.1, 0.001)
        self.rotate_regulator = PDRegulator(1.4, 0.001)

        self.depth_regulator = PDRegulator(70, 20)
        self.side_regulator = PDRegulator(0.5, 1)
        self.side_depth_regulator = PDRegulator(0.15, 1)
        
        self.delta_angle = 0
        self.count_stable = 0

        self.is_at_target = False

        self.cache_motor = {
            '0': 0,
            '1': 0,
            '2': 0,
            '3': 0,
            '4': 0,
        }

    @staticmethod
    def __clamp(value, min_value, max_value):
        # Функция для ограничения значения в заданном диапазоне
        
        return min(max(value, min_value), max_value)

    @staticmethod
    def get_delta(x, y, img_shape) -> tuple:
        # Функция для вычисления разницы (x, y) с центром изображения и заданными координатами, и отклонение по углу
        
        img_center = (img_shape[0] // 2, img_shape[1] // 2)

        delta_x = img_center[0] - x
        delta_y = img_center[1] - y
        delta_angle = -atan2(delta_x, delta_y) * 180 / pi

        return delta_x, delta_y, delta_angle
    
    def go_to_point(self, x, y, half_img, delta_k=50, move_side_k=2.5, error=10, speed=60):
        depth = self.get_depth()

        lr_mode = -1 if half_img - x < 0 else 1
        delta_x = (half_img - x) ** 2 // delta_k * lr_mode
        depth += (-half_img + y) * 0.003

        self.move_side(delta_x*move_side_k, y-half_img)
        if abs(delta_x) < error:
            self.keep_yaw(-delta_x, speed)

        else:
            self.keep_yaw(-half_img + x, 10)

        return depth
    
    # def keep_yaw(self, yaw_to_set: float|int, speed):
    def keep_yaw(self, yaw_to_set, speed):
        # Функция для поддержания заданного курса при определенной скорости движения вперед/назад

        const_clamp = 100

        error = self.auv.get_yaw() - yaw_to_set
        if error > 180.0:
            return error - 360.0
        if error < -180.0:
            return error + 360

        output = self.yaw_regulator.process(error)
        time.sleep(self.SLEEP)

        self.set_motor(0, self.__clamp(int(-output + speed), -const_clamp, const_clamp))
        self.set_motor(1, self.__clamp(int(output + speed), -const_clamp, const_clamp))

        return error

    def keep_depth(self, depth_to_set, kd=0.7):
        # Функция для поддержания заданной глубины

        error = (self.auv.get_depth() - depth_to_set) * kd
        output = self.depth_regulator.process(error)
        time.sleep(self.SLEEP)
        output = self.__clamp(int(output), -40, 40)

        for n_motor in (2, 3):
            self.set_motor(n_motor, output)

        return error
    
    def move_side(self, delta_x, delta_y):
        # Функция для движения в сторону

        x_output = self.side_regulator.process(delta_x)
        y_output = self.side_depth_regulator.process(delta_y)

        x_output = self.__clamp(int(x_output), -70, 70)
        y_output = self.__clamp(int(y_output), -40, 40)

        time.sleep(self.SLEEP)

        for n_motor in (2, 3):
            self.set_motor(n_motor, y_output)

        self.set_motor(4, x_output)

    def sideways_movement(self, x, y, half_img):
        is_end = True

        if not self.is_at_target:
            delta_x = half_img - x
            delta_y = (half_img - y) * 0.005
            if 0 < abs(delta_y) < 4 and 0 < abs(delta_x) < 4:
                self.is_at_target = True
            else:
                is_end = False

            self.move_side(delta_x, delta_y)

        return is_end

    def follow_line(self, delta_y, angle):
        # Шорткат для движения по линии

        self.keep_yaw(self.auv.get_yaw() + angle, (80 + delta_y) * 0.05)

    def get_yaw(self):
        return self.auv.get_yaw()
    
    def get_depth(self):
        return self.auv.get_depth()

    def shoot(self):
        self.auv.shoot()

    def drop(self):
        self.auv.drop()

    def set_motor(self, number, speed):
        prev_speed = self.cache_motor.get(str(number))

        if prev_speed != speed:
            self.auv.set_motor_power(number, speed*1.05)
            self.cache_motor[str(number)] = speed*1.1

    def move_forward_backward(self, speed=0):
        self.set_motor(0, speed)
        self.set_motor(1, speed)

    def rotate(self, angle, error_max=5):
        error = self.auv.get_yaw() - angle
        # if error > 180.0:
        #     error -= 360.0
        # if error < -180.0:
        #     return error + 360

        output = self.rotate_regulator.process(error)
        time.sleep(self.SLEEP)

        self.set_motor(0, self.__clamp(int(-output), -40, 40))
        self.set_motor(1, self.__clamp(int(output), -40, 40))

        delta_angle = angle - self.get_yaw()

        if abs(delta_angle) < error_max:
            self.count_stable += 1
            self.delta_angle = (self.delta_angle + delta_angle) / self.count_stable
            if self.count_stable == 50:
                if abs(self.delta_angle) < 3:
                    return True
        else:
            self.count_stable = 0
            self.delta_angle = 0

        return False