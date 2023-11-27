import time
import traceback
from enum import Enum, auto
from config import Config


def _auto_enumerate():
    # no inspection PyArgumentList
    return auto()


# for debug
class SRC(Enum):
    GUI = _auto_enumerate()
    DATASET = _auto_enumerate()
    GENERAL = _auto_enumerate()
    CLIP = _auto_enumerate()
    POPUP_WIN = _auto_enumerate()
    CONFIG = _auto_enumerate()


def image_resize_size(hw=(400, 400), max_hw=(400, 400)):
    """
    Returns a size that keeps the ratio of "hw" but does not exceed "max_hw"
    """
    if min(max_hw) < 280:
        return -1
    wrad = hw[0] / max_hw[0]
    hrad = hw[1] / max_hw[1]
    # padding by 5
    pad = 0
    # (w, h)
    p1 = (int(hw[1] // wrad) - pad, int(hw[0] / wrad) - pad)
    p2 = (int(hw[1] // hrad) - pad, int(hw[0] / hrad) - pad)

    if p1[0] <= max_hw[1] and p1[1] <= max_hw[0]:
        if p2[0] <= max_hw[1] and p2[1] <= max_hw[0]:
            res = max(p1, p2)
        else:
            res = p1
    else:
        res = p2

    return res


def load_ca(W, H):
    t, l, b, r = int(H / 5), int(W / 5), int(4 * H / 5), int(4 * W / 5)

    return [l, t, r, b]


# def save_ca(W, H):
#     t, l, b, r = int(H / 4), int(W / 4), int(3 * H / 4), int(3 * W / 4)
#     try:
#         with open(Config.CHECKAREA_DATA, 'w') as f:
#             f.write(f"{t} {l} {b} {r}")
#
#     except (FileNotFoundError, ValueError):
#         # traceback.print_exc()
#         pass
#
#     return [t, l, b, r]


class TokaiDebug:
    def __init__(self):
        self.bar_time = 0.
        self.tag_time = 0.
        self.yolo_time = 0.
        self.total_time = 0.
        self.bar_cnt = 0.
        self.tag_cnt = 0.
        self.yolo_cnt = 0.
        self.bar_time_start = 0.
        self.tag_time_start = 0.

    def bar_start(self):
        self.bar_time_start = time.time()
        self.bar_cnt += 1

    def bar_end(self):
        self.bar_time += time.time() - self.bar_time_start

    def get_bar_time(self):
        return "{:.5f}".format(self.bar_time / self.bar_cnt) if self.bar_cnt > 0 else "NO BAR"

    def tag_start(self):
        self.tag_time_start = time.time()
        self.tag_cnt += 1

    def tag_end(self):
        self.tag_time += time.time() - self.tag_time_start

    def get_tag_time(self):
        return "{:.5f}".format(self.tag_time / self.tag_cnt) if self.tag_cnt > 0 else "NO TAG"

    def yolo_start(self):
        self.yolo_time_start = time.time()
        self.total_time_start = time.time()
        self.yolo_cnt += 1

    def yolo_end(self):
        self.yolo_time += time.time() - self.yolo_time_start

    def get_yolo_time(self):
        return "{:.5f}".format(self.yolo_time / self.yolo_cnt) if self.yolo_cnt > 0 else "NO YOLO"

    def total_end(self):
        self.total_time = max(self.total_time, time.time() - self.total_time_start)
        # self.total_time += time.time() - self.total_time_start

    def get_total_time(self):
        # y = self.yolo_time / self.yolo_cnt if self.yolo_cnt > 0 else 0
        # b = self.bar_time / self.bar_cnt if self.bar_cnt > 0 else 0
        # t = self.tag_time / self.tag_cnt if self.tag_cnt > 0 else 0

        return "{:.5f}".format(self.total_time)
        # return "{:.5f}".format(self.total_time / self.yolo_cnt) if self.yolo_cnt > 0 else "NO TOTAL"


tokai_debug = TokaiDebug()
