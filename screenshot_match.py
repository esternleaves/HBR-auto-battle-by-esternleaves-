import numpy as np
import cv2
import os
import time

from typing import Union
from ctypes import windll, c_ubyte
from ctypes.wintypes import HWND
from numpy import uint8, frombuffer
from keyboard import press_and_release

from global_data import search_range, resource_path, ppp, get_time_str, get_tem_array
from presets_read import output_battle_list, get_sp_check_list
# 图片截取和识图部分

root_path = resource_path["root_path"]

window_size = search_range["window_size"]
right_part_window = search_range["right_part_window"]
skill_available_rcg_thresh = ppp["skill_available_rcg_thresh"]

# 判断回合开始的识图区域
start_action_range = search_range["start_action"]
exit_or_change_team_range = search_range["exit_or_change_team"]
battle_result_range = search_range["battle_result"]

# 判断技能能否使用的识图区域,和od等级
range_list = [search_range["skill_1"], search_range["skill_2"], search_range["skill_3"]]

od_0 = cv2.imdecode(buf=np.fromfile(file=resource_path["od_0"], dtype=np.uint8), flags=-1)
od_1 = cv2.imdecode(buf=np.fromfile(file=resource_path["od_1"], dtype=np.uint8), flags=-1)
od_2 = cv2.imdecode(buf=np.fromfile(file=resource_path["od_2"], dtype=np.uint8), flags=-1)
od_3 = cv2.imdecode(buf=np.fromfile(file=resource_path["od_3"], dtype=np.uint8), flags=-1)
od_list = [od_0, od_1, od_2, od_3]

# 把四个要高频识别的图片和四个od状态模版先加载一下,免得经常读文件了
start_action_array_template = cv2.imdecode(
    buf=np.fromfile(file=resource_path["start_action"], dtype=np.uint8), flags=-1)

exit_array_template = cv2.imdecode(
    buf=np.fromfile(file=resource_path["exit"], dtype=np.uint8), flags=-1)

change_team_array_template = cv2.imdecode(
    buf=np.fromfile(file=resource_path["change_team"], dtype=np.uint8), flags=-1)

battle_result_array_template = cv2.imdecode(
    buf=np.fromfile(file=resource_path["battle_result"], dtype=np.uint8), flags=-1)

battle_failed_array_template = cv2.imdecode(
    buf=np.fromfile(file=resource_path["battle_failed"], dtype=np.uint8), flags=-1)

default_battle_failed_rcg_flag: bool = True  # 是否为默认战斗失败识别
battle_failed_rcg_range = start_action_range  # 默认检查'主画面',和start_action按钮一个范围


def update_battle_failed_rcg(template_count: int = 0):
    """更新不同的识别战斗失败模版"""
    global battle_failed_array_template
    global default_battle_failed_rcg_flag
    global battle_failed_rcg_range
    if template_count > 0:  # 更新战斗失败识图模版
        default_battle_failed_rcg_flag = False
        battle_failed_rcg_range = search_range["battle_failed_" + str(template_count)]
        battle_failed_array_template = cv2.imdecode(
            buf=np.fromfile(file=resource_path["battle_failed_" + str(template_count)], dtype=np.uint8), flags=-1)
    elif not default_battle_failed_rcg_flag:  # 切回默认模版
        default_battle_failed_rcg_flag = True
        battle_failed_rcg_range = start_action_range
        battle_failed_array_template = cv2.imdecode(
            buf=np.fromfile(file=resource_path["battle_failed"], dtype=np.uint8), flags=-1)


# 截图函数
def capture_image_png(raw_range: list, handle: HWND = None) -> np.ndarray:
    """
    对hbr的steam窗口进行截图时,handle必须为None.必须前台截图,该窗口已屏蔽api接口,截得的图全黑或不会变化.
    :param raw_range: 屏幕坐标, [左上X, 左上Y,右下X, 右下Y]
    :param handle: 窗口句柄,handle为None则截取前台
    :return: 截图数据 3D array (高度,宽度,[B G R A 四通道])
    """
    width, height = raw_range[2] - raw_range[0], raw_range[3] - raw_range[1]  # 客户区宽度和高度

    # 创建设备上下文
    dc = windll.user32.GetDC(handle)  # 获取窗口的设备上下文
    cdc = windll.gdi32.CreateCompatibleDC(dc)  # 创建一个与给定设备兼容的内存设备上下文
    bitmap = windll.gdi32.CreateCompatibleBitmap(dc, width, height)  # 创建兼容位图
    windll.gdi32.SelectObject(cdc, bitmap)  # 将位图选入到内存设备上下文中，准备绘图

    # 执行位块传输，将窗口客户区的内容复制到内存设备上下文中的位图
    windll.gdi32.BitBlt(cdc, 0, 0, width, height, dc, raw_range[0], raw_range[1], 0x00CC0020)

    # 准备缓冲区，用于接收位图的像素数据
    total_bytes = width * height * 4  # 计算总字节数，每个像素4字节（RGBA）
    buffer = bytearray(total_bytes)  # 创建字节数组作为缓冲区
    byte_array = c_ubyte * total_bytes  # 定义C类型数组类型

    # 从位图中获取像素数据到缓冲区
    windll.gdi32.GetBitmapBits(bitmap, total_bytes, byte_array.from_buffer(buffer))

    # 清理资源
    windll.gdi32.DeleteObject(bitmap)  # 删除位图对象
    windll.gdi32.DeleteObject(cdc)  # 删除内存设备上下文
    windll.user32.ReleaseDC(handle, dc)  # 释放窗口的设备上下文

    # 将缓冲区数据转换为numpy数组，并重塑为图像的形状 (高度,宽度,[B G R A四通道])
    image = frombuffer(buffer, dtype=uint8).reshape(height, width, 4)

    return image


def capture_image_png_b_and_w(raw_range: list, thresh: int = 254) -> np.ndarray:
    """截图转黑白,thresh为前景阈值,默认用于高亮sp数字识别，高亮部分为255"""
    image = capture_image_png(raw_range)
    img1 = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # 处理成黑白简单识别高光数字
    img2 = cv2.threshold(img1, thresh, 255, cv2.THRESH_BINARY)[1]
    return np.dstack([img2]*3)


# 识图函数
def match_template_with_optional_mask(img_source, img_template) -> np.ndarray:
    """
    使用可选掩模进行模板匹配。

    如果模板图像包含Alpha通道且不是纯白，则使用该Alpha通道作为掩模进行匹配。
    如果模板图像不包含Alpha通道或Alpha通道为纯白，则直接进行匹配。

    Args:
        img_source (numpy.ndarray): 源图像。
        img_template (numpy.ndarray): 模板图像，可能包含Alpha通道作为掩模。

    Returns:
        numpy.ndarray: 匹配结果。
    函数:对应方法 匹配良好输出->匹配不好输出
        CV_TM_SQDIFF:平方差匹配法 [1]->[0]；
        CV_TM_SQDIFF_NORMED:归一化平方差匹配法 [0]->[1]；
        CV_TM_CCORR:相关匹配法 [较大值]->[0]；
        CV_TM_CCORR_NORMED:归一化相关匹配法 [1]->[0]；
        CV_TM_CCOEFF:系数匹配法；
        CV_TM_CCOEFF_NORMED:归一化相关系数匹配法 [1]->[0]->[-1]

        # 检查模板图像是否包含Alpha通道
    """
    method = cv2.TM_SQDIFF_NORMED
    # 检查模板图像是否包含Alpha通道
    if img_template.shape[2] == 4:
        # 提取Alpha通道作为掩模
        mask = img_template[:, :, 3]
        # 移除Alpha通道，保留RGB部分
        img_template = img_template[:, :, :3]

        # 检查掩模是否为纯白
        if not np.all(mask == 255):
            # 掩模非纯白，使用掩模进行匹配
            result = cv2.matchTemplate(image=img_source, templ=img_template, method=method, mask=mask)
            return result

    # 对于不包含Alpha通道或Alpha通道为纯白的情况，直接进行匹配
    result = cv2.matchTemplate(image=img_source, templ=img_template, method=method)
    return result


def match_p_in_w(template,
                 image_array: np.ndarray = None,
                 source_range: list = None,
                 handle=None,
                 match_tolerance: float = 0.95,
                 is_test: bool = False) -> Union[None, list]:
    """
    find target in template
    catch an image by a handle, find a smaller image(target) in this bigger one, return center relative position
    :param template: 目标图片的文件路径或ndarray模版
    :param image_array: 已经截取的图片3D array [B G R A]四通道或[B G R]三通道
    :param source_range: 识别的图像在屏幕中的范围,为 [左上X, 左上Y,右下X, 右下Y], 右下位置超出范围取最大(不会报错)
    :param handle: 窗口句柄,没有则识别屏幕前台
    :param match_tolerance: 捕捉准确度阈值 0-1
    :param is_test:是否测试
    Returns: 识别到的目标的中心坐标(相对于截图后)
    """
    if not (image_array is None):
        img_source = image_array[:, :, :3]
    elif source_range:
        img_source = capture_image_png(raw_range=source_range, handle=handle)
        img_source = img_source[:, :, :3]
    else:
        return None

    # 根据 路径 或者 numpy.array 选择是否读取
    if type(template) is np.ndarray:
        img_template = template
    else:
        # 读取目标图像,中文路径兼容方案
        img_template = cv2.imdecode(buf=np.fromfile(file=template, dtype=np.uint8), flags=-1)

    # 自定义的模板匹配
    result = match_template_with_optional_mask(img_source=img_source, img_template=img_template)
    (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(src=result)
    if is_test:
        print(1 - minVal)

    # 如果匹配度<阈值,就认为没有找到
    if minVal >= 1 - match_tolerance:
        return None

    # 最优匹配的左上坐标
    (start_x, start_y) = minLoc

    # 输出识别到的中心
    center_point = [
        start_x + int(img_template.shape[1] / 2),
        start_y + int(img_template.shape[0] / 2)
    ]
    return center_point


def match_ps_in_w(
        template_opts: list,
        image_source: np.ndarray = None,
        source_range: list = None,
        handle=None,
        match_tolerance: float = 0.95) -> Union[None, list]:
    """
    匹配多个图片
    :param template_opts: 模版路径列表
    :param source_range: 匹配范围,[左上X, 左上Y,右下X, 右下Y],
    :param match_tolerance: 匹配度
    :param handle: 窗口句柄,没有则识别屏幕前台
    :param image_source: 图源
    :return: result len(template_opts) * ([None] or [[number_point_x, number_point_y]])  (1D/2D list)
    """

    if not (image_source is None):
        source_img = image_source[:, :, :3]
    elif source_range:
        source_img = capture_image_png(raw_range=source_range, handle=handle)
        source_img = source_img[:, :, :3]
    else:
        return None

    result_list = []

    for p in range(len(template_opts)):
        result = match_p_in_w(
            template=template_opts[p],
            match_tolerance=match_tolerance,
            source_range=source_range,
            image_array=source_img
        )
        result_list.append(result)

    if result_list:
        return result_list
    else:
        return None


def png_cropping(image, raw_range: list):
    return image[raw_range[1]:raw_range[3], raw_range[0]:raw_range[2], :]


# 自编部分
def is_likely_gray(img_source: np.ndarray) -> bool:
    """快速通过图上5点判断是否开了灰色滤镜"""
    shape = img_source.shape
    point = [img_source[int(shape[0] / 2)][int(shape[1] / 2)], img_source[int(shape[0] / 4)][int(shape[1] / 4)],
             img_source[int(shape[0] / 4 * 3)][int(shape[1] / 4)], img_source[int(shape[0] / 4)][int(shape[1] / 4 * 3)],
             img_source[int(shape[0] / 4 * 3)][int(shape[1] / 4 * 3)]]
    for i in range(5):
        if point[i][0] != point[i][1] or point[i][0] != point[i][2]:
            return False
    return True


def edge_is_likely_gray(img_source: np.ndarray) -> bool:
    """主要通过图片边缘的点判定是否开了灰色滤镜,例如od按钮等图片中心颜色大致相同的模版识别需要此函数"""
    shape = img_source.shape
    point = [img_source[int(shape[0] / 2)][int(shape[1] / 2)], img_source[0][int(shape[1] / 4)],
             img_source[int(shape[0] - 1)][int(shape[1] / 4)], img_source[0][int(shape[1] / 4 * 3)],
             img_source[int(shape[0] - 1)][int(shape[1] / 4 * 3)]]
    for i in range(5):
        if point[i][0] != point[i][1] or point[i][0] != point[i][2]:
            return False
    return True


def cvt_tmp_gray(template: np.ndarray) -> np.ndarray:
    """把BGR三通道彩色图转为三通道灰度图,适配黑白模式读取"""
    return np.dstack([cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)]*3)


def verify_start_flag(gray_flag: bool = False) -> Union[bool, int, None]:
    """
    母函数初步检测到start_action按钮亮起后,详细核实目前行动状态的函数,双重确认保证行动开始不出错
    :param gray_flag: 是否开了灰度模式,由初步检测的母函数给出
    :return: 可以行动(exit按钮和start_action按钮同时亮起返回True,change_team按钮和start_action按钮同时亮起返回2),
    不可行动(仍需等待返回None)
    """
    img_exit_or_change_team = capture_image_png(exit_or_change_team_range)[:, :, :3]

    if gray_flag:  # 如果认为开了黑白模式,把模版处理成灰度模式
        if match_p_in_w(template=cvt_tmp_gray(exit_array_template), image_array=img_exit_or_change_team):
            return True
        elif match_p_in_w(template=cvt_tmp_gray(change_team_array_template), image_array=img_exit_or_change_team):
            return 2
        else:
            return None
    else:
        if match_p_in_w(template=exit_array_template, image_array=img_exit_or_change_team):
            return True
        elif match_p_in_w(template=change_team_array_template, image_array=img_exit_or_change_team):
            return 2
        else:
            return None


def get_start_flag() -> Union[bool, int, None]:
    """
    检测角色能否行动,根据结果进行下一动,二重确认保证行动开始不出错,较省系统资源.兼容颜色滤镜黑白模式.
    首先初步截图判断start_action按钮是否亮起,亮起根据verify_start_flag确认详细状态,若上一个函数返回None说明初步识图出错;
    其次判断'主画面'按钮是否亮起,亮起说明战斗失败强制退回主画面,返回False;
    若start_action和'主画面'按钮都未亮起,返回None,使程序继续等待.
    :return: 可以行动(exit按钮和start_action按钮同时亮起返回True,change_team按钮和start_action按钮同时亮起返回2),
    不可行动(检测到主画面按钮亮起,认为战斗失败返回False;仍需等待返回None)
    """
    if default_battle_failed_rcg_flag:  # 默认战斗失败模版'主画面',和start_action按钮一个范围
        img_likely_start = img_battle_failed = capture_image_png(start_action_range)[:, :, :3]  # 尝试截图一个很小的区域初步检测
    else:  # 自定义了新的战斗失败模版,识别游戏全屏
        img_battle_failed = capture_image_png(window_size)[:, :, :3]
        img_likely_start = png_cropping(img_battle_failed, start_action_range)

    gray_flag: bool = is_likely_gray(img_likely_start)

    if gray_flag:  # 开了黑白模式
        if match_p_in_w(template=cvt_tmp_gray(start_action_array_template), image_array=img_likely_start):  # 初步检测一下
            if verify_flag := verify_start_flag(gray_flag):
                return verify_flag
            else:
                return None  # 初步检测错误,继续等待
        elif match_p_in_w(template=cvt_tmp_gray(battle_failed_array_template), image_array=img_battle_failed):
            return False  # 检测到主画面按钮,认为战斗已经失败
        else:
            return None  # 没有检测到,继续等待
    else:  # 正常彩色模式
        if match_p_in_w(template=start_action_array_template, image_array=img_likely_start):
            if verify_flag := verify_start_flag(gray_flag):
                return verify_flag
            else:
                return None
        elif match_p_in_w(template=battle_failed_array_template, image_array=img_battle_failed):
            return False  # 检测到主画面按钮,认为战斗已经失败
        else:
            return None


def is_likely_start_and_is_powerful_enemy() -> list:
    """
    道中判断战斗是否开始,及遭遇的是否是精英敌人,用于在连续战斗模式的等待时间(例如跑废墟)节省识图资源的写法
    :return: 1D list [战斗是否开始: bool, 是否遭遇了精英敌人: bool]
    """

    def point_powerful_enemy(img_is_powerful_enemy: np.ndarray) -> bool:
        """判断是否遭遇精英敌人,精英敌人的全红图片转灰度后全屏都是125,沿用start_action按钮的检测范围
        根据划X的部分抽样判断灰度图片是否几乎全部都是,允许一定数量噪点,start_action按钮截图大小为160*170"""
        img_point_powerful_enemy = cv2.cvtColor(img_is_powerful_enemy, cv2.COLOR_BGR2GRAY)
        shape = [160, 170]
        non_125_point: int = 0
        for i in range(shape[0]):
            if img_point_powerful_enemy[30][i] != 125:
                non_125_point += 1
            elif img_point_powerful_enemy[80][i] != 125:
                non_125_point += 1
        if non_125_point > 5:  # 避免一些诡异动画的噪点,实测识图start_action范围的160*170一般稳定在0个点左右
            return False
        else:
            return True

    img_likely_start = capture_image_png(start_action_range)[:, :, :3]

    is_powerful_enemy_flag: bool = point_powerful_enemy(img_likely_start)

    gray_flag: bool = is_likely_gray(img_likely_start)

    if gray_flag:
        start_action_button_array = cvt_tmp_gray(start_action_array_template)
    else:
        start_action_button_array = start_action_array_template

    if match_p_in_w(template=start_action_button_array, image_array=img_likely_start):
        if verify_start_flag(gray_flag):  # 初步判断完成后再全游戏界面截图识别三个图
            start_flag: bool = True
        else:
            start_flag: bool = False
    else:
        start_flag: bool = False

    # print([start_flag, is_powerful_enemy_flag])

    return [start_flag, is_powerful_enemy_flag]


def defalult_recognition(image_name: str,
                         img_range: list = None,
                         match_tolerance: float = 0.95) -> Union[None, list]:
    """
    本程序默认识图函数,要求在resource文件中存image_file_name.png一张模版,
    若图片位于resource文件的子文件夹下,image_name中需要包含子文件夹路径
    自定义在search_range中有无专用识图区域,没有定义就识别整个hbr窗口,识别到电脑开黑白模式则匹配黑白模版
    :param image_name: png图片的名字(不含.png),如果在resource的子文件夹下,需要包含子文件夹路径
    :param img_range: 识别范围,没有就识别窗口全屏
    :param match_tolerance: 识别准确度阈值 0-1
    :return: 图片在截图区域的坐标
        if img_range is None:  # 暂时不用的函数
        file_name = image_name.split("\\")[-1]
        img_range = search_range.setdefault(file_name, window_size)
    """
    if img_range is None:  # 路径里包含了母文件夹名,所以set_default没用了
        img_range = window_size

    img_array = capture_image_png(img_range)[:, :, :3]  # 去掉透明度图层
    img_array_template = get_tem_array(image_name)

    if is_likely_gray(img_array):  # 如果认为开了黑白模式,把模版处理成灰度模式
        img_array_template = cvt_tmp_gray(img_array_template)

    if result := match_p_in_w(image_array=img_array,
                              template=img_array_template,
                              match_tolerance=match_tolerance):
        # print("找到了", image_name)
        return [result[0] + img_range[0], result[1] + img_range[1]]
    else:
        return None


def rcg_battle_result():
    """识别有没有战斗奖励结算环节,有则说明战斗结束"""
    return defalult_recognition("battle_result", search_range["battle_result"])


def score_attack_result_recognition(match_tolerance: float = 0.95) -> Union[None, list]:
    """识别打分出分界面的识图标签"""
    return defalult_recognition("screenshot_score_attack",
                                search_range["screenshot_score_attack"],
                                match_tolerance=match_tolerance)


def rcg_daily_rewards(check_times: int = 6, is_test: bool = False):
    """每天凌晨退掉奖励领取部分"""
    daily_rewards_flag: bool = False  # 判断识图超时是因为出现了每日奖励界面,还是确实出现了掉线等情况
    for i in range(check_times):  # 默认检查六轮,不会有那么多每日奖励弹窗吧
        if defalult_recognition("daily_rewards", search_range["daily_rewards"]):
            if is_test:
                print("检测到无阴影skip")
            else:
                press_and_release("esc")
            daily_rewards_flag: bool = True
        elif defalult_recognition("daily_rewards_shadow", search_range["daily_rewards_shadow"]):
            if is_test:
                print("检测到无阴影skip")
            else:
                press_and_release("esc")
            daily_rewards_flag: bool = True
        elif is_test:
            print("本轮未检测到skip按钮")
        time.sleep(3)
    return daily_rewards_flag


def get_od_level() -> int:
    """
    获得当前od等级
    :return:
    """
    img_od = capture_image_png(search_range["od"])
    list_level = od_list

    if edge_is_likely_gray(img_od):
        for tem_od_count in range(len(list_level)):
            list_level[tem_od_count] = cvt_tmp_gray(list_level[tem_od_count])

    result_od = match_ps_in_w(list_level,
                              source_range=search_range["od"])

    level_now: int = 0
    for level_1 in range(4):
        if result_od[level_1]:
            level_now = level_1

    return level_now


def use_od(od_level: int = 1):
    """当目前的od等级大于等于od_level时,开od"""
    if od_level == 0:
        press_and_release("o")
        time.sleep(1)
    else:
        if get_od_level() >= od_level:
            press_and_release("o")
            time.sleep(1)


def is_skill_can_use(skill_order, thresh: int = skill_available_rcg_thresh) -> bool:
    """
    判断技能是否能使用
    :param skill_order: 用的是从上到下第几个技能,只允许1,2,3.0为普攻,必然返回True
    :param thresh: 黑白前后景阈值
    :return: 是否能使用
    """

    def is_skill_img_not_black(img_source: np.ndarray) -> bool:
        """根据两行判断图片是否全黑,允许一定数量噪点"""
        non_black_point: int = 0
        for i in range(50):
            if img_source[i][i] != 0:
                non_black_point += 1
            elif img_source[i][49 - i] != 0:
                non_black_point += 1
        if non_black_point > 4:  # 避免一些诡异动画的噪点
            return True
        else:
            return False

    skill_order = int(skill_order)

    if skill_order in [1, 2, 3]:
        img_is_skill_can_use = capture_image_png(range_list[skill_order - 1])
        img_is_skill_can_use = cv2.cvtColor(img_is_skill_can_use, cv2.COLOR_BGR2GRAY)  # 处理成黑白简单识别高光数字
        img_is_skill_can_use = cv2.threshold(img_is_skill_can_use, thresh, 255, cv2.THRESH_BINARY)[1]
        return is_skill_img_not_black(img_is_skill_can_use)
    elif skill_order == 0:
        return True
    else:
        img_is_skill_can_use = capture_image_png(range_list[2])  # 4以上的选之前都用键盘输入到3位
        img_is_skill_can_use = cv2.cvtColor(img_is_skill_can_use, cv2.COLOR_BGR2GRAY)  # 处理成黑白简单识别高光数字
        img_is_skill_can_use = cv2.threshold(img_is_skill_can_use, thresh, 255, cv2.THRESH_BINARY)[1]
        return is_skill_img_not_black(img_is_skill_can_use)


def extra_mode_101() -> None:
    """截图下面这个打分结算识别的标签"""
    img_mvp_1 = capture_image_png(search_range["1_mvp"])
    img_mvp_2 = capture_image_png(search_range["2_mvp"])
    img_mvp_3 = capture_image_png(search_range["3_mvp"])
    img_mvp_4 = capture_image_png(search_range["4_mvp"])
    cv2.imwrite("1.png", img_mvp_1)
    cv2.imwrite("2.png", img_mvp_2)
    cv2.imwrite("3.png", img_mvp_3)
    cv2.imwrite("4.png", img_mvp_4)


def save_enemy_label():
    path_enemy_label = os.path.join(root_path, "resource", "enemy_label-battle_preset", get_time_str(True) + ".png")
    enemy_label = capture_image_png_b_and_w(search_range["enemy_label"], 232)
    cv2.imwrite(path_enemy_label, enemy_label)


def screenshot_score_attack() -> None:
    """自动打分模式,识图截图,上面这个函数返回True后自动截图保存"""
    image = capture_image_png(search_range["window_size"])
    path = os.path.join(resource_path["score_attack"], get_time_str(True) + ".png")
    cv2.imwrite(path, image)


def return_list_by_enemy_label(label_range: list = window_size,
                               path_in_resource: str = "enemy_label-battle_preset",
                               match_tolerance: float = 0.96,
                               is_test: bool = False,
                               default_sp_check_return: bool = True) -> list:
    """
    长线战斗识图选战斗方案,如果在识别到start_action按钮亮起时识别到了名为battle_preset.png的敌人标签,
    则返回的result[0]为battle_preset文件夹中battle_preset.txt内的战斗方案,没有则执行0.txt的战斗方案
    返回的result[1]为battle_preset文件夹中sp_check-battle_preset.txt内的战斗方案,没有则为None
    :param label_range: 搜索敌人标签的范围(遭遇战中为最高分词条范围)
    :param path_in_resource: 搜索图片位于resource的哪个子文件夹
    :param match_tolerance: 匹配度
    :param is_test: 是否调试
    :param default_sp_check_return: 无sp检查则返回默认
    :return: 找到了,返回2D/1D list:[战斗方案, sp检查方案, [图片x坐标, 图片y坐标]/None]
    """
    def return_default() -> list:
        battle_preset_default = output_battle_list("0")
        sp_check_default = get_sp_check_list()
        return [battle_preset_default, sp_check_default, None]

    path_root = os.path.join(root_path, "resource", path_in_resource)

    file_list = os.listdir(path_root)  # 获取全部文件名
    model_path_list = []
    name_list = []

    for file in file_list:
        model_path_list = model_path_list + [os.path.join(path_root, file)]
        name_list = name_list + [str(file).replace(".png", "")]  # 去掉.png后缀

    match_list = match_ps_in_w(template_opts=model_path_list,
                               source_range=label_range,
                               match_tolerance=match_tolerance)

    if is_test:
        print("model_path_list", model_path_list)
        print(name_list)
        print(match_list)

    if match_list:
        for card_order in range(len(match_list)):
            if match_list[card_order]:  # 输出匹配到的图片对应的battle_preset
                battle_preset_path = os.path.join(root_path, "battle_presets", name_list[card_order] + ".txt")
                if os.path.exists(battle_preset_path):
                    battle_preset = output_battle_list(name_list[card_order])  # 战斗方案
                    sp_check_preset = get_sp_check_list(name_list[card_order], default_return=default_sp_check_return)
                    return_list = [battle_preset, sp_check_preset, match_list[card_order]]
                    if is_test:
                        print(return_list)
                        print(match_list[card_order])
                    return return_list
                else:
                    return return_default()
        return return_default()
    else:
        return return_default()


def get_sss_sp_check_list(floor_sp: int, preset_name: str) -> Union[None, list]:
    path_sp_check_0 = os.path.join("seraph_skirmish_sim_sp_check", str(floor_sp), preset_name)
    path_sp_check = os.path.join(root_path, "program_parameter_presets", "img_rcg_reaction",
                                 path_sp_check_0 + ".txt")
    if os.path.exists(path_sp_check):
        sss_sp_check_list = get_sp_check_list(path_sp_check_0, default_return=False)
        return sss_sp_check_list
    else:
        return None


def seraph_skirmish_sim_recognize(floor: int,
                                  refresh_time: int = 0,
                                  match_tolerance: float = 0.96) -> Union[None, list]:
    """
    炽天使遭遇战识图选战斗方案,floor为当前在第几层,sp_check-" + str(preset_name) + ".txt
    如果在floor楼选牌时识别到了名为battle_preset.png的图片,
    则返回的result[0]为battle_preset文件夹中battle_preset.txt内的战斗方案
    返回的result[1]为battle_preset文件夹中sp_check-battle_preset.txt内的战斗方案,没有则为[]
    禁止开黑白模式识图
    :param floor: 现在在几楼
    :param refresh_time: 剩余刷新次数
    :param match_tolerance: 匹配度
    :return: 找到了,返回1D list:[战斗方案, sp检查方案, [词条图片x坐标, 词条图片y坐标], 剩余刷新次数],
    没有则返回1D list:[1f战斗方案, 1fsp检查方案, None, 0]
    """
    path_in_resource = os.path.join("seraph_skirmish_sim", str(floor))

    for i in range(refresh_time):
        result_list = return_list_by_enemy_label(window_size, path_in_resource,
                                                 match_tolerance=match_tolerance)
        if not result_list[2]:
            press_and_release("r")
            refresh_time = refresh_time - 1
            time.sleep(2)
        else:
            break

    result_list = return_list_by_enemy_label(window_size, path_in_resource, match_tolerance=match_tolerance)

    if result_list[2]:
        return_list = result_list
    else:
        battle_preset_first_floor = output_battle_list("seraph_skirmish_sim_1f")
        return_list = [battle_preset_first_floor, result_list[1], False]
    if refresh_time:
        return return_list + [refresh_time]
    else:
        return return_list + [0]


if __name__ == '__main__':
    time.sleep(2)
    aaa = seraph_skirmish_sim_recognize(1,5)
    print(aaa)
