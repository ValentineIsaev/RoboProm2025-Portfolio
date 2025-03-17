
import cv2
import numpy as np
from math import atan2, pi


FRAME_SIZE = (500, 500)

MASKS = {
    "orange": ((0, 80, 165), (200, 215, 200)),
    "pink":   ((0, 150, 0), (255, 255, 105)),
    'purple': ((0, 105, 0), (100, 255, 105)),
    'green': ((135,0,150),(235,180,180)),              # ((135,0,150),(230,190,190))
    'red': ((50,150,150),(100, 230, 255)),
    'gray': ((150, 120, 120),(220, 220, 220))
}


class Eyes:

    def __init__(self):
        self._frame = None
        self._bin_frame = None

    def text_on_frame(self, *args, size=1):
        for i in range(0, len(args), 2):
            if i != len(args):
                text = args[i]
                position = args[i+1]
                cv2.putText(self._frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, size, (0, 255, 0), 2)

    def show_image(self, window_name, delay=1, show_thresh=False):
        # Show the image
        img = self._frame

        if show_thresh:
            if not self._bin_frame is None:
                cv2.imshow(window_name, self._bin_frame)
            # img = np.hstack((
            #     img,
            #     cv2.cvtColor(self._bin_frame, cv2.COLOR_GRAY2BGR)))
        else:
            cv2.imshow(window_name, img)
        cv2.waitKey(delay)

    def show_time(self, time: float):
        canvas = np.zeros((200, 200, 3), dtype=np.uint8)

        cv2.putText(canvas, str(time), (80, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        cv2.imshow('TIME', canvas)
        cv2.waitKey(1)

    def add_new_frame(self, frame):
        # Save new frame in class

        blur_frame = cv2.GaussianBlur(frame, (1, 1), 1)
        normalize_frame = cv2.resize(blur_frame, FRAME_SIZE)

        self._frame = normalize_frame

    def _mask(self, color, inverse=False):
        # Making binary frame

        lab = cv2.cvtColor(self._frame, cv2.COLOR_BGR2LAB)

        thresh = cv2.inRange(lab, MASKS[color][0], MASKS[color][1])
        
        if inverse: thresh = (255 - thresh)

        self._bin_frame = thresh

    def _get_contour(self, a_min, _a_max, angles: tuple = None):
        # Find contours and their selection

        contours, _ = cv2.findContours(self._bin_frame, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        selection_contours = []
        for cnt in contours:
            angles_mode = True
            area = cv2.contourArea(cnt)
            if angles:
                perimeter = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.04 * perimeter, True)
                if not angles[1] >= len(approx) >= angles[0]:
                    angles_mode = False

            if a_min < area < _a_max and angles_mode:
                selection_contours.append(cnt)

        return selection_contours
    
    
    def detect_arrow(self):
        self._mask('orange')

        size = self._frame.shape[1], self._frame.shape[0]

        contours = self._get_contour(100, 50000)

        if len(contours) == 0: return (None, None, None)

        cnt = sorted(contours, 
                     key=lambda cnt: cv2.contourArea(cnt), 
                     reverse=True)[0]

        # Наивысшая точка(нос стрелки)
        x1, y1 = sorted(cnt, key=lambda p: p[0][1])[0][0]

        # Вспомогательная точка
        x2, y2 = size[0] // 2, sorted(cnt, 
                        key=lambda p: 
                        abs(p[0][0] - size[0] // 2))[-1][0][1]


        x3, y3 = x1, y2

        cv2.circle(self._frame, (x1, y1), 5, (255, 0, 0), -1)
        cv2.circle(self._frame, (x2, y2), 5, (0, 255, 0), -1)
        cv2.circle(self._frame, (x3, y3), 5, (0, 0, 255), -1)

        delta_x, delta_y = x3 - x2, y3 - y1

        delta_angle = atan2(delta_x, delta_y) * 180 / pi

        # print(delta_x, delta_x, delta_angle)


        self.show_image('ARROW', show_thresh=True)
        self.show_image('ARROW2', show_thresh=False)

        return (delta_x, delta_y, delta_angle)

    def mask_and_sum(self, mask):
        self._mask(mask)
        return np.sum(self._bin_frame)//255

    def sum_mask(self, threshold, mask, mode='[]'):
        if mode == '[]':
            condition = self.mask_and_sum(mask) >= threshold
        elif mode == '()':
            condition = self.mask_and_sum(mask) > threshold
        elif mode == '=':
            condition = self.mask_and_sum(mask) == threshold
        else:
            raise ValueError('WRONG MODE!')

        return condition


class FrontEye(Eyes):
    def __init__(self):
        super().__init__()

        self.search_on = True
    
    def find_yellow_square(self):
        self._mask('orange', inverse=True)

        img_center = (self._frame.shape[1] // 2, self._frame.shape[0] // 2)
        contours = sorted(self._get_contour(600, 80000, angles=(4, 6)), key=lambda cnt: cnt[0][0][0])
        
        if len(contours) == 0: return None, None, None

        # cnt = contours[0]
        cnt = contours[-1]

        x, y, w, h = cv2.boundingRect(cnt)
        x, y = x + w // 2, y + h // 2
        delta_x = img_center[0] - x
        delta_y = img_center[1] - y

        area = cv2.contourArea(cnt)

        return area, delta_x, delta_y
    
    def find_pink_circle(self):
        self._mask('pink', inverse=True)
        
        img_center = (self._frame.shape[1] // 2, self._frame.shape[0] // 2)
        contours = self._get_contour(600, 200000, angles=(5, 20)) 

        if len(contours) == 0: return (None, None, None)

        cnt = sorted(contours,
                     key = lambda cnt: cv2.contourArea(cnt),
                     reverse = True)[0]
        
        area = cv2.contourArea(cnt)

        x, y, w, h = cv2.boundingRect(cnt)
        x, y = x + w // 2, y + h // 2

        delta_x = img_center[0] - x
        delta_y = img_center[1] - y

        return delta_x, delta_y, area

    def search_points_screws(self, mode: str):
        self._mask('green')
        contours = self._get_contour(1200, 10*10**4)

        if mode != 'LEN_CNT':
            modes = {'LEFT': False,
                     'RIGHT': True}
            reverse = modes.get(mode)

            coordinates_points = []
            if contours and self.search_on:
                for cnt in contours:
                    x, y, w, h = cv2.boundingRect(cnt)
                    coordinates_points.append([x+w//2, y+h//2, 'GO'])
                    # cv2.rectangle(self._frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                coordinates_points = sorted(coordinates_points, key=lambda p: p[0], reverse=reverse)

            elif np.sum(self._bin_frame) > 100*10**3: # or not self.search_on:
                coordinates_points.append([250, 250, 'SLOWING'])
                if self.search_on:
                    self.search_on = False

            elif self.sum_mask(480*490, 'red'):
                # print('RED!RED!')
                coordinates_points.append([250, 250, "STOP"])

            else:
                return []

            # if coordinates_points:
            #     cv2.circle(self._frame, coordinates_points[0][:2], 5, (0, 0, 255), -1)
            # cv2.circle(self._frame, (250, 250), 5, (255, 0, 0), -1)
            # self.show_image('BIN', show_thresh=True)

            return coordinates_points[0]
        else:
            return len(contours)

    def is_distance_gray_screw(self, threshold):
        self._frame[350:, :] = [0,0,0]
        self._mask('gray')

        # self.text_on_frame(str(np.sum(self._bin_frame)//255), (0, 100))
        # self.show_image('BIN', show_thresh=True)
        # self.show_image('ORIGINAL')

        if np.sum(self._bin_frame)//255 < threshold:
            return True
        return False


class BottomEye(Eyes):
    def __init__(self):
        super().__init__()

    def detect_line(self, rotate=False):
        # Возвращает x, y, их нужно передать
        # в Move.get_delta, её результат(delta_y, delta_angle) в Move.follow_line

        self._mask('purple')

        if rotate:
            self._bin_frame = cv2.rotate(self._bin_frame, cv2.ROTATE_90_CLOCKWISE)
        
        # Чтобы робот не срезал путь
        cv2.rectangle(self._bin_frame, (0, 0), (self._frame.shape[1], 60), (0, 0, 0), -1)
        cv2.rectangle(self._bin_frame, (0, self._frame.shape[0] - 150), (self._frame.shape[1], self._frame.shape[0]), (0, 0, 0), -1)

        contours = self._get_contour(600, 80000, angles=(2, 10))

        if len(contours) == 0: return (None, None, self._frame.shape[::-1])

        cnt = sorted(contours, key=lambda cnt: cnt[0][0][1])[0] # Поиск самого высокого контура

        rect = cv2.minAreaRect(cnt)
        box = cv2.boxPoints(rect)
        box = np.int0(box)

        x, y = min(box, key=lambda point: point[1])

        # cv2.drawContours(self._frame, [box], 0, (0, 0, 255), 2)
        # cv2.circle(self._frame, (x, y), 5, (0, 255, 255), -1)
        # self.show_image('bottom_eye', show_thresh=True)

        return x, y, self._bin_frame.shape[::-1]

    def detect_red_circle(self):
        self._mask('red')

        cv2.rectangle(self._bin_frame, (0, 0), 
                      (self._bin_frame.shape[1], 
                       self._bin_frame.shape[0]), 
                       (0, 0, 0), 1)
        
        contours = self._get_contour(100, 100000)

        if len(contours) == 0: return (None, None)

        cnt = sorted(contours, 
                     key=lambda cnt: cv2.contourArea(cnt),
                     reverse=True)[0]
        
        x, y, w, h = cv2.boundingRect(cnt)

        x, y = x + w//2, y + h//2

        # cv2.circle(self._frame, (x, y), 5, (0, 255, 0), -1)
        
        # cv2.drawContours(self._frame, [cnt], 0, (0, 255, 0), 2)

        # self.show_image('bottom_eye1', show_thresh=True)
        # self.show_image('bottom_eye2')

        return (x, y)


vision = (FrontEye(), BottomEye())
