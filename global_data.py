import os.path

import win32gui
import win32con
import time
import cv2
import numpy as np
from path_lib import resource_path
from presets_read import read_program_presets


root_path = resource_path["root_path"]


def hbr_get_handle():
    """获取窗口句柄，返回句柄"""
    return win32gui.FindWindow(None, "HeavenBurnsRed")


def awaken_hbr_window(handle):
    """通过系统函数或鼠标点击把hbr窗口拉到前台，调试时改注释掉上一行
    原因是我在用pycharm内测试时win32gui.SetForegroundWindow(handle)随机报错
    (大概率,可能同样代码1分钟前不报下一次就报了),测试时就鼠标点击唤醒到前台了.
    exe中不会像py内一样报错,我也不知道为什么
    """
    win32gui.SetWindowPos(handle, None, 0, 0, 0, 0, win32con.SWP_NOSIZE)
    win32gui.SetForegroundWindow(handle)


def get_time_str(is_file_name: bool = False) -> str:
    """获得时间字符串,True时返回能作为文件名保存的字符串"""
    time_second = time.time()
    local_time = time.localtime(time_second)
    if is_file_name:
        return time.strftime("%Y-%m-%d_%H-%M-%S", local_time)
    else:
        return time.strftime("%Y-%m-%d %H:%M:%S", local_time)


def get_tem_array(file_relative_path: str):
    """
    把读取完的模版加进内存,避免反复读取
    :param file_relative_path: 图片模版相对于resource文件夹的路径,不需要带.png
    :return: 模版的 3D array (高度,宽度,[B G R 三通道])
    """
    if file_relative_path in tem_array_pool:
        return tem_array_pool[file_relative_path]
    else:
        tem_path = os.path.join(root_path, "resource", file_relative_path + ".png")
        tem_array = cv2.imdecode(buf=np.fromfile(file=tem_path, dtype=np.uint8), flags=-1)
        tem_array_pool[file_relative_path] = tem_array
        return tem_array


# 下面的全局变量和两个函数是在1280*720解析度下有关识图点击的坐标,调整这些参量可以用于其他的解析度
search_range = {  # 按钮检索范围,节省识图资源,同时加快识图打轴速度,懒就直接window_size,本程序适用于1280*720
    # 程序本体各运行模式运行必须
    "window_size": [0, 0, 1320, 760],  # 整个游戏屏幕的大小
    "right_part_window": [610, 0, 1320, 760],
    "start_action": [1100, 540, 1260, 710],  # start_action按钮检索范围,节省识图资源
    "exit_or_change_team": [45, 35, 120, 100],  # 退出按钮和换队按钮位置
    "sss_highest_score": [700, 200, 1050, 600],  # 炽天使遭遇战,只识别最高分数词条的范围
    "od": [1140, 50, 1240, 130],
    "skill_1": [480, 170, 530, 220],  # 第一个技能位是否高亮(能使用)的识图范围,函数固定适配50*50,约用0.02s
    "skill_2": [435, 290, 485, 340],
    "skill_3": [415, 410, 465, 460],
    "battle_failed_1": [0, 0, 1320, 760],  # 自定义失败识图模版范围,识别战斗是否失败,识别整个游戏窗口
    "battle_failed_5": [1090, 560, 1320, 760],  # 自定义失败识图模版范围,识别战斗是否失败,识别整个游戏窗口
    "battle_failed_9": [380, 310, 930, 410],  # 异时层识别战斗是否失败范围(game over)
    "daily_rewards": [1050, 30, 1270, 110],  # 每日登录奖励的弹出的skip按钮位置
    "daily_rewards_shadow": [1050, 30, 1270, 110],
    "auto_off_sss_battle": [0, 30, 230, 120],
    # sp识别,其他模式调用必须
    "1_mvp": [96, 116, 190, 189],  # 1号位mvp标签的范围
    "2_mvp": [59, 197, 158, 270],  # 2号位mvp标签的范围
    "3_mvp": [38, 281, 137, 357],  # 3号位mvp标签的范围
    "4_mvp": [37, 372, 133, 446],  # 4号位mvp标签的范围
    "1_sp": [130, 550, 185, 600],  # 从左到右第1个人的sp检索位置
    "2_sp": [330, 550, 385, 600],  # 从左到右第2个人的sp检索位置
    "3_sp": [515, 550, 575, 600],  # 从左到右第3个人的sp检索位置
    "4_sp": [700, 570, 745, 600],  # 从左到右第4个人的sp检索位置
    "5_sp": [860, 570, 905, 600],  # 从左到右第5个人的sp检索位置
    "6_sp": [1020, 570, 1065, 600],  # 从左到右第6个人的sp检索位置
    "enemy_label": [1000, 155, 1210, 175],  # 敌人标签字体范围
    # 下面的这些理论上都可以删掉,会自动识别全屏
    "battle_result": [50, 40, 180, 105],
    "screenshot_score_attack": [25, 100, 200, 455],  # 打分mvp识图标签
    "exclamation_tip": [0, 50, 1280, 360],  # 打分和钟楼进入关卡的感叹号框识别,上半屏幕,避免打分重开识别到黑猫的对话框
    "fight_bell_tower": [735, 595, 880, 675],
    "attack": [600, 635, 710, 720],  # 异时层里attack按钮字间距更大,其他正常界面相同
    "challenge_score_attack": [800, 600, 1080, 700],  # 挑战按钮
    "divergence_0": [510, 380, 675, 435],  # 点开项目后的异时层小标签,由于不能截到剩余票数,太小了必须要限定范围
    "divergence": [95, 40, 230, 130],  # 异时层
    "challenge_divergence": [800, 600, 1080, 700],  # 挑战按钮
    "practice_mode": [550, 510, 720, 575],
    "ok": [645, 410, 1270, 740],
    "start_next_sss_battle": [1100, 600, 1250, 680],
    "0_level": [420, 645, 490, 690],  # 异时层梦泪增强等级,需要指定范围,不然图片太小有可能识别不到
    "1_level": [420, 645, 490, 690],  # 异时层梦泪增强等级
    "2_level": [420, 645, 490, 690],  # 异时层梦泪增强等级
    "3_level": [420, 645, 490, 690],  # 异时层梦泪增强等级
    "4_level": [420, 645, 490, 690],  # 异时层梦泪增强等级
    "5_level": [420, 645, 490, 690],  # 异时层梦泪增强等级
}
click_point = {
    # 一个都不能少
    "start_action": [1180, 620],  # start_action按钮位置
    "empty_position": [40, 150],  # 空位置,要求没有任何按钮,用来清除技能选择状态,点击关闭战斗奖励结算界面用
    "empty_position_in_sss_battle": [40, 250],
    "auto": [245, 70],  # auto按钮,用于在技能使用时发现sp不够时自动开auto模式
    "normal_full": [[390, 70], [510, 70]],  # auto开什么模式
}


def get_location(order: int) -> list:
    """返回点击坐标，己方从左到右编号为1,2,3,4,5,6,
    敌方单位分别为8,9,7三体)/8,7(双体),0为默认不选择,省时间则点击0"""
    if order == 1:
        return [120, 630]
    elif order == 2:
        return [310, 630]
    elif order == 3:
        return [510, 630]
    elif order == 4:
        return [690, 630]
    elif order == 5:
        return [850, 630]
    elif order == 6:
        return [1010, 630]
    elif order == 8:  # 左侧敌人
        return [675, 400]
    elif order == 9:  # 中间敌人/无敌人
        return [885, 400]
    elif order == 7:  # 右侧敌人
        return [1110, 400]
    else:
        return [0, 0]


def skill_position(skill_order: int) -> list:
    """根据skill_order返回从上到下三个技能位置的点击坐标,若skill_order不是1-3,则选择普通攻击"""
    if skill_order == 1:  # 调整这些数值时,注意兼顾other["switch_skill_target_x_offset"]点击的切换技能位置
        return [500, 200]
    elif skill_order == 2:
        return [478, 325]
    elif skill_order == 3:
        return [456, 450]
    else:
        return [170, 465]


ppp = {#读取program_parameter_presets参数
    # 是否调试
    "is_test": read_program_presets(
        "is_test", True, True)[0],
    # 战斗内外识图频率
    "search_frequency": read_program_presets(
        "search_frequency", True)[0],
    "recognize_button_circle": read_program_presets(
        "search_frequency", True)[1],
    # 读取无限循环打分标签识图的自定义匹配度
    "match_tolerance_special_1": read_program_presets(
        "match_tolerance_special_1", True, False)[0],
    # 一动限时,超出认为被打死
    "action_time_limit": read_program_presets(
        "action_time_limit", True, False)[0],
    # 读取先开od后检测sp时的等待时间
    "click_od_time_before_sp_check": read_program_presets(
        "action_time_limit", True, False)[1],
    # 技能可用性识别阈值
    "skill_available_rcg_thresh": read_program_presets(
        "skill_available_rcg_thresh", True, True)[0],
}

tem_array_pool = {  # 存储已读过文件的template array

}
