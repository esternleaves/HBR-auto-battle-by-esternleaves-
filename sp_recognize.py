import cv2
import numpy as np
from typing import Union
from path_lib import number_rear_template_path_list, number_front_template_path_list
from global_data import search_range
from screenshot_match import capture_image_png_b_and_w, match_ps_in_w


# 预加载一下模版的list,注意不同数字的模版尺寸不同,不能用array存,数字"1"的模版不能截得跟其他数字一样大,不然识别到后的涂黑环节中会涂掉相邻数字
# 前排数字,字体稍大
img_array_front_template_list = []
for front_template in range(len(number_front_template_path_list)):
    img_front_template = cv2.imdecode(
        buf=np.fromfile(file=number_front_template_path_list[front_template], dtype=np.uint8), flags=-1)
    img_array_front_template_list.append(img_front_template)
# 后排数字
img_array_rear_template_list = []
for rear_template in range(len(number_rear_template_path_list)):
    img_rear_template = cv2.imdecode(
        buf=np.fromfile(file=number_rear_template_path_list[rear_template], dtype=np.uint8), flags=-1)
    img_array_rear_template_list.append(img_rear_template)


def get_sp_if_can_use_skill(search_range: list,
                            match_template_path: list,
                            match_tolerance: float = 0.75) -> Union[int, None]:  # sp识图函数
    """
    如果角色的sp可以使用技能(数字高光),返回sp,反之返回none,暂时还无法识别欠费但可使用技能的情况(那也就一个港孔)\n
    注意,如果数字1的模版截掉了边框的黑色部分,会把数字4的一竖识别成1,考虑扩充数字1的模版的宽度,使之和其他数字宽度差不多
    :param search_range: 搜索数字的范围
    :param match_template_path: 数字模版的路径列表
    :param match_tolerance: 匹配度
    :return: 如果角色的sp可以使用技能(数字高光),返回sp,反之返回none,暂时还无法识别欠费
    """

    def make_number_list(input_list) -> list:
        """
        翻译识图得到的坐标列表,得到数字坐标列表
        :param input_list: match_ps_in_w得到的识图坐标列表
        :return: 若干项的数字列表,子列表[x,y,z]中,x为模版在路径列表中的编号.y,z为识别到的坐标,由于模版10个一组,x%10就是模版上的数字
        """
        number_list = []
        for i_0 in range(len(input_list)):  # 识别以10个数为一组的多套模版,防止重复识别
            if input_list[i_0]:
                if i_0 % 10 == i_0:
                    number_list.append([i_0, input_list[i_0][0], input_list[i_0][1]])
                else:
                    append_flag = True
                    j_0 = i_0 - 10
                    while j_0 >= 0:
                        if input_list[j_0]:
                            append_flag = False
                        j_0 = j_0 - 10
                    if append_flag:  # 如果前面的同类模版都没有识别成功,就加进去,避免重复识别
                        number_list.append([i_0, input_list[i_0][0], input_list[i_0][1]])
        return number_list

    sp_image_source = capture_image_png_b_and_w(search_range)

    result_list = match_ps_in_w(
        template_opts=match_template_path,
        source_range=search_range,
        match_tolerance=match_tolerance,
        image_source=sp_image_source)
    number_list = make_number_list(result_list)

    # if is_test: print("result_list=", result_list) print("number_list=", number_list)

    if len(number_list) == 2:  # 识别到两个不同的数字,谁在左边谁就是十位,如果有更多位,以下写成递归函数
        if number_list[0][1] > number_list[1][1]:  # 取余是因为存在多组每组为10个的模版
            return (number_list[0][0] % 10)+(number_list[1][0] % 10)*10
        else:
            return (number_list[0][0] % 10)*10+(number_list[1][0] % 10)
    elif len(number_list) == 1:  # 有可能是两个数字一样,把刚才识别到的部分涂黑,再识别一次
        model_shape = match_template_path[number_list[0][0]].shape  # 获取模版大小,避免涂黑不必要的区域
        for i in range(number_list[0][2] - (int(model_shape[0]/2)+2),
                       number_list[0][2] + (int(model_shape[0]/2)+2)):
            for j in range(number_list[0][1] - (int(model_shape[1]/2)+2),
                           number_list[0][1] + (int(model_shape[1]/2)+2)):
                sp_image_source[i][j] = [0, 0, 0]  # 按模版大小涂黑已识别内容,涂的范围稍微大一点,+1到+3,

        result_list_1 = match_ps_in_w(
            template_opts=match_template_path,
            source_range=search_range,
            match_tolerance=match_tolerance,
            image_source=sp_image_source)
        number_list_1 = make_number_list(result_list_1)

        if len(number_list_1):  # 有两个一模一样的数字,返回两位数sp,谁在左边谁是10位
            if number_list[0][1] > number_list_1[0][1]:
                return (number_list[0][0] % 10) + (number_list_1[0][0] % 10) * 10
            else:
                return (number_list[0][0] % 10) * 10 + (number_list_1[0][0] % 10)
        else:  # 确实只有一个数字,返回sp
            return number_list[0][0] % 10
    else:
        return None


def get_sp(recognize_order: int,
           match_tolerance=0.8) -> Union[int, None]:
    """
    如果从左到右第recognize_order个角色可以释放技能,返回其现在的sp
    :param recognize_order: 需要匹配的角色编号,从左到右为123456
    :param match_tolerance: 匹配度
    :return: 角色的sp
    """
    if recognize_order == 1:
        sp = get_sp_if_can_use_skill(
            search_range["1_sp"], img_array_front_template_list, match_tolerance=match_tolerance)
    elif recognize_order == 2:
        sp = get_sp_if_can_use_skill(
            search_range["2_sp"], img_array_front_template_list, match_tolerance=match_tolerance)
    elif recognize_order == 3:
        sp = get_sp_if_can_use_skill(
            search_range["3_sp"], img_array_front_template_list, match_tolerance=match_tolerance)
    elif recognize_order == 4:
        sp = get_sp_if_can_use_skill(
            search_range["4_sp"], img_array_rear_template_list, match_tolerance=match_tolerance)
    elif recognize_order == 5:
        sp = get_sp_if_can_use_skill(
            search_range["5_sp"], img_array_rear_template_list, match_tolerance=match_tolerance)
    elif recognize_order == 6:
        sp = get_sp_if_can_use_skill(
            search_range["6_sp"], img_array_rear_template_list, match_tolerance=match_tolerance)
    else:
        sp = None
    return sp


def return_now_order(initial_order, order_of_stations) -> int:
    """返回进场编号为initial_order的角色现在的位置编号,从左到右分别为1,2,3,4,5,6,或返回敌人的位置编号
    order_of_stations[a],order_of_stations[b] = order_of_stations[b],order_of_stations[a]
    """
    for now_order_of_stations in range(6):
        if order_of_stations[now_order_of_stations] == initial_order:
            return now_order_of_stations + 1  # 己方实际位置是数组序号+1


def get_sp_through_initial_position(initial_order_of_station: int,
                                    order_of_stations: list = None,
                                    match_tolerance=0.75) -> Union[int, None]:
    """
    获得初始站位为initial_order_of_station的角色目前的sp,本文件唯一被引用的函数
    :param initial_order_of_station: 进场编号,即初始站位
    :param order_of_stations: 所有队伍目前的站位,取0位前台队伍
    :param match_tolerance: 匹配度
    :return: sp值int
    """
    if order_of_stations is None:
        order_of_stations = [1, 2, 3, 4, 5, 6]
    order_now = return_now_order(initial_order_of_station, order_of_stations)
    sp = get_sp(order_now, match_tolerance=match_tolerance)
    return sp
