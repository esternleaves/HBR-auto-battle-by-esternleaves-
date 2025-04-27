import ctypes
from ctypes import windll
from time import sleep

# 鼠标函数


def mouse_move(x: int, y: int):
    """将鼠标移动到屏幕绝对坐标(x, y)点处(左上角为 0,0)"""
    ctypes.windll.user32.SetCursorPos(x, y)


def mouse_handle_click(handle, x: int, y: int, interval_time=0.05, sleep_time=0.1):
    """
    给定坐标在坐标(x, y)点击(按下 休息 放开)
    Args:
        handle: 窗口句柄
        x: 横坐标
        y: 纵坐标
        interval_time: 按住的时间
        sleep_time: 点击后休息的时间
    """
    windll.user32.PostMessageW(handle, 0x0201, 0, y << 16 | x)
    sleep(interval_time)
    windll.user32.PostMessageW(handle, 0x0202, 0, y << 16 | x)
    sleep(sleep_time)


def hbr_left_click(handle, x_y: list, interval_time=0.05, sleep_time=0.1):
    """
    hbr窗口点击必须要有句柄,并移动鼠标激活窗口的二级鼠标才能点成功
    :param handle: 窗口句柄
    :param x_y: 点击(x, y)
    :param interval_time: 按住的时间
    :param sleep_time: 点击后休息的时间
    :return:
    """
    mouse_move(x_y[0], x_y[1])
    sleep(0.05)
    mouse_handle_click(handle, x_y[0], x_y[1], interval_time, sleep_time)
