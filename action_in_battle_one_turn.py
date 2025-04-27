from keyboard import press_and_release, press, release
from time import sleep
from ctypes.wintypes import HWND

from mouse import hbr_left_click
from global_data import click_point, get_location, skill_position, ppp
from screenshot_match import is_skill_can_use, get_start_flag
# 一动的机械部分 sleep时间太短容易让hbr窗口还没反应过来,纯键盘也容易报错,这是比较稳定的
recognize_button_circle = ppp["recognize_button_circle"]  # 识别技能使用按钮可用性的频率


def return_now_order(initial_order, order_of_stations: list) -> int:
    """返回进场编号为initial_order的角色现在的位置编号,从左到右分别为1,2,3,4,5,6,或返回敌人的位置编号
    order_of_stations[a],order_of_stations[b] = order_of_stations[b],order_of_stations[a]
    """
    if initial_order < 7:  # 返回己方
        for now_order_of_stations in range(6):
            if order_of_stations[now_order_of_stations] == initial_order:
                return now_order_of_stations + 1  # 己方实际位置是数组序号+1
    else:  # 返回敌人编号
        return initial_order


def swap_role_by_initial_order(handle: HWND, x_order: int, y_initial_order: int, order_of_stations):
    """进场时，所有角色从左到右编号为1,2,3,4,5,6,将目前x_order位的角色与进场编号y_initial_order的角色交换。"""
    y_now_order = return_now_order(y_initial_order, order_of_stations)  # 编号为y_initial_order的角色目前的站位
    if x_order != y_now_order:
        hbr_left_click(handle, click_point["empty_position"])
        sleep(0.1)
        hbr_left_click(handle, get_location(y_now_order))
        sleep(0.1)
        hbr_left_click(handle, get_location(x_order))
        order_of_stations[x_order - 1], order_of_stations[y_now_order - 1] = order_of_stations[y_now_order - 1], \
            order_of_stations[x_order - 1]  # 数组要-1
        sleep(0.1)


def choose_skill_and_select_target(handle: HWND,
                                   order_of_stations,
                                   role_order: int,
                                   skill_order0: float,
                                   skill_target: int) -> bool:
    """
    使用从左到右数第role_order位角色的第skill_order个技能,释放给skill_target目标
    :param handle: 窗口句柄
    :param order_of_stations: 角色站位
    :param role_order: 角色序号
    :param skill_order0: 技能序号
    :param skill_target: 技能目标
    :return: 是否使用成功
    """

    if (skill_order0 - int(skill_order0)) == 0.5:  # 如果需要切换技能的话
        switch_skill_flag: bool = True
    else:
        switch_skill_flag: bool = False
    skill_order = int(skill_order0)

    hbr_left_click(handle, click_point["empty_position"])  # 清除状态
    sleep(0.1)
    hbr_left_click(handle, get_location(role_order))  # 点击角色
    sleep(recognize_button_circle)  # 多等一会儿,不要技能框没加载出来就识别了

    if switch_skill_flag:  # 切技能
        for i in range(skill_order):
            press_and_release("s")
            sleep(0.2)
        sleep(0.2)
        if is_skill_can_use(3):
            press_and_release("Tab")
            sleep(0.4)
            press_and_release("Enter")
            sleep(0.1)
        else:
            press_and_release("Esc")
            return False
    else:
        if skill_order < 4:
            if is_skill_can_use(skill_order):
                hbr_left_click(handle, skill_position(skill_order))
            else:
                press_and_release("Esc")
                return False
        else:  # 如果选择大于3的技能,鼠标逐个拖动,键盘输入用win32api都无效
            for i in range(skill_order):  # api接口被屏蔽,这是调用系统底层驱动的库
                press_and_release("s")
                sleep(0.2)
            sleep(0.2)
            if is_skill_can_use(3):
                hbr_left_click(handle, skill_position(3))
            else:
                press_and_release("Esc")
                return False
        sleep(0.1)
        if skill_target != 0:  # 选择施放目标
            hbr_left_click(handle, get_location(return_now_order(skill_target, order_of_stations)))
            sleep(0.1)
    return True


def auto_if_skill_could_not_use(handle, auto_full: bool = True):
    """
    自动开auto模式
    :param handle: 窗口句柄
    :param auto_full: False则开auto normal
    :return: None
    """
    sleep(0.5)
    hbr_left_click(handle, click_point["auto"])
    sleep(0.3)
    hbr_left_click(handle, click_point["normal_full"][int(auto_full)])
    sleep(2.2)
    hbr_left_click(handle, click_point["auto"])


def action_in_battle_one_turn(handle: HWND,
                              action: list,
                              order_of_stations: list,
                              if_action: bool = True) -> bool:
    """
    action数组转换为行动的接口,先换位再选技能,不然有些人切到后排后技能会释放失败
    :param handle: 句柄
    :param action: 一个行动的1d list
    :param order_of_stations: 站位
    :param if_action: 是否正常行动,False就自动开auto模式
    :return: 是否正常操作(开了auto认为非正常操作)
    """
    if if_action:
        skill_flag: bool = True
        if action[1] != 0:
            swap_role_by_initial_order(handle, 1, int(action[1]), order_of_stations)
        if action[4] != 0:
            swap_role_by_initial_order(handle, 2, int(action[4]), order_of_stations)
        if action[7] != 0:
            swap_role_by_initial_order(handle, 3, int(action[7]), order_of_stations)
        if action[1] != 0:
            if not choose_skill_and_select_target(handle, order_of_stations, 1, action[2], int(action[3])):
                skill_flag = False
        if action[4] != 0:
            if not choose_skill_and_select_target(handle, order_of_stations, 2, action[5], int(action[6])):
                skill_flag = False
        if action[7] != 0:
            if not choose_skill_and_select_target(handle, order_of_stations, 3, action[8], int(action[9])):
                skill_flag = False
    else:
        skill_flag: bool = False
    return skill_flag


def clear_skill_use(handle, order_of_stations, check_list_this_turn: list = None):
    """在后开od后检测sp时,若检查角色处于前排,可能残留od前选取的技能,在sp检查前清空角色的技能选择情况
    check_list_this_turn = [[检查回合(首回合为1),角色1的进场编号,角色1正确的sp值],[回合,角色2......]]
    """
    if check_list_this_turn:  # 只清空前排需要检查的人的技能选取,加快速度
        for role in range(len(check_list_this_turn)):
            order = return_now_order(check_list_this_turn[role][1], order_of_stations)
            if order <= 3:
                choose_skill_and_select_target(handle, order_of_stations, order, 0, 0)
    else:  # 单纯前排全选普攻
        choose_skill_and_select_target(handle, order_of_stations, 1, 0, 0)
        choose_skill_and_select_target(handle, order_of_stations, 2, 0, 0)
        choose_skill_and_select_target(handle, order_of_stations, 3, 0, 0)


def press_key(string_key: str, press_time=0.15, sleep_time=0.1):
    """跳剧情按ctrl用的"""
    press(string_key)
    sleep(press_time)
    release(string_key)
    sleep(sleep_time)


def press_key_list(key_list, p_s: float = 0.4):
    for press_event in range(len(key_list)):
        sleep(p_s)  # 识到图了不等于你马上能点
        press_and_release(key_list[press_event])


def change_team() -> None:
    """检测到换队列表[2,0,0,0,0,0,0,0,0,0]的换队操作"""
    if get_start_flag() is True:  # True返回没有换队按钮
        return None
    else:  # 返回2,说明有换队按钮
        while get_start_flag():
            press_key_list(["Esc", "Enter", "Esc"])
