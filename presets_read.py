import numpy as np
import os
from path_lib import resource_path

root_path_0 = resource_path["root_path"]


# 预设txt读取部分
def read_file(file_path: str, open_encoding=None):
    """读文件"""
    if os.path.exists(file_path):
        file = open(file_path, "r", encoding=open_encoding)
        file_content = file.read()
        file.close()  # 关闭避免内存泄露
        return file_content
    else:
        return None


def save_file(file_path: str, save_content):
    """保存文件,没有就创建一个新的保存"""
    if os.path.exists(file_path):
        file_save = open(file_path, "w", encoding='utf-8')
        file_save.write(save_content)
        file_save.close()
    else:
        with open(file_path, 'w', encoding='utf-8') as file_save:
            file_save.write(save_content)


def get_preset_path(file_name: str,
                    is_program_presets: bool = False,
                    is_img_rcg_reaction: bool = False) -> str:
    """
    获取预设文件路径
        :param file_name: str,例如1.txt只需要输入"1"
        :param is_program_presets: 系统预设/战斗方案预设
        :param is_img_rcg_reaction: 是否读取识图结果相关预设
        :return: path
        """
    if is_img_rcg_reaction:
        file_name = os.path.join("img_rcg_reaction", file_name)
    if is_program_presets:
        return os.path.join(root_path_0, "program_parameter_presets", file_name + ".txt")
    else:
        return os.path.join(root_path_0, "battle_presets", file_name + ".txt")


def read_presets(txt_file_name,
                 is_program_presets=False,
                 open_type_encoding=None) -> list:
    """
    :param txt_file_name: str,例如1.txt只需要输入"1"
    :param is_program_presets: 系统预设/战斗方案预设
    :param open_type_encoding: 打开中文文档时,open_type_encoding='utf-8'
    :return: 读取后的逐行字符串列表
    """
    file_path = get_preset_path(txt_file_name, is_program_presets)
    if os.path.exists(file_path):
        file = open(file_path, "r", encoding=open_type_encoding)
        presets_file = file.readlines()
        file.close()  # 关闭避免内存泄露
        return presets_file
    else:
        return []


def read_program_presets(txt_file_name,
                         is_program_presets=True,
                         if_return_int=False,
                         open_type_encoding=None) -> np.ndarray:
    """从txt文档内读取程序的运行参数"""
    file_read = read_presets(txt_file_name=txt_file_name,
                             is_program_presets=is_program_presets,
                             open_type_encoding=open_type_encoding)
    if if_return_int:
        return np.array(file_read, dtype=int)
    else:
        return np.array(file_read, dtype=float)


def save_program_presets(txt_file_name,
                         is_program_presets=True,
                         if_return_int=False,
                         open_type_encoding=None) -> np.ndarray:
    """从txt文档内读取程序的运行参数"""
    file_read = read_presets(txt_file_name=txt_file_name,
                             is_program_presets=is_program_presets,
                             open_type_encoding=open_type_encoding)
    if if_return_int:
        return np.array(file_read, dtype=int)
    else:
        return np.array(file_read, dtype=float)


# 做全队battle_list
def remove_enter_and_space_and_make_battle_list(original_list,
                                                return_int_list=True,
                                                list_lenth: int = 10) -> list:
    """
    返回移除original_list中无效的换行转义字符\n和空格后的有效int列表,后参数若为False,返回float列表
    :param original_list: 从文件逐行读取的字符串列表
    :param return_int_list: 返回的列表是否为整数列表,False则返回float列表
    :param list_lenth: 读取的列表长度
    :return: 返回一个队伍移除original_list中无效的换行转义字符\n和空格后的有效列表(2D list)
    """
    original_lenth = len(original_list)
    if return_int_list:  # 默认返回int
        output_original_array = np.zeros((original_lenth, list_lenth), int)
    else:
        output_original_array = np.zeros((original_lenth, list_lenth), float)
    output_effective_count = 0  # 有效的矩阵数
    for effective_count in range(original_lenth):
        original_list_str = str(original_list[effective_count]).strip()  # 防止手贱在txt下面多打回车+空格导致程序错误
        if len(original_list_str) != 0:
            if return_int_list:  # 默认返回int
                output_original_array[output_effective_count] = np.array(original_list_str.split(','), int)  # 把字符串内空格去掉
            else:
                output_original_array[output_effective_count] = np.array(original_list_str.split(','), float)
            output_effective_count = output_effective_count + 1
    if return_int_list:  # 默认返回int
        output_array = np.zeros((output_effective_count, list_lenth), int)
    else:
        output_array = np.zeros((output_effective_count, list_lenth), float)
    for effective_count_1 in range(output_effective_count):  # 不拷贝只有回车和空格的行
        output_array[effective_count_1] = output_original_array[effective_count_1]
    return output_array.tolist()


def make_list_all_teams(txt_file_read_result,
                        list_lenth,
                        return_int_list=True) -> list:
    """
    制作多队的战斗列表,队与队之间以空行分隔
    :param txt_file_read_result: 从文件逐行读取的字符串列表
    :param list_lenth: 列表长度
    :param return_int_list: 返回的列表是整数列表还是float列表
    :return: 多队的战斗列表(3D list)
    """
    list_all_team = []
    list_one_team = []
    read_lenth = len(txt_file_read_result)
    for i in range(read_lenth):
        if txt_file_read_result[i].replace(" ", "") == '\n':  # 免得手贱在回车后面打空格报错
            if list_one_team:
                append_list = remove_enter_and_space_and_make_battle_list(
                    list_one_team, return_int_list=return_int_list, list_lenth=list_lenth)
                list_all_team.append(append_list)
                list_one_team = []
        else:
            list_one_team.append(txt_file_read_result[i])
    if list_one_team:
        append_list = remove_enter_and_space_and_make_battle_list(
            list_one_team, return_int_list=return_int_list, list_lenth=list_lenth)
        list_all_team.append(append_list)
    return list_all_team


# 全队战斗方案
def output_battle_list(battle_list_input_str) -> list:
    """
    :param battle_list_input_str: 根据输入的txt文件名输出全部队伍的battle_list
    :return: 多队battle_list(也可以只有一队)
    """
    battle_list_file_read = read_presets(str(battle_list_input_str), is_program_presets=False)
    return make_list_all_teams(battle_list_file_read, list_lenth=10, return_int_list=False)


# 全队sp检查列表
def get_sp_check_list(img_recognize_file_name: str = None, default_return: bool = True) -> list | None:
    """
    获取sp检查列表,如果没有指定文件名("sp_check-" + str(preset_name) + ".txt"),获取默认
    :param img_recognize_file_name: img_rcg_sp_check文件夹中预设img_recognize_file_name.txt对应的sp检查方案,包含上一级文件路径
    :param default_return: 如果预设文件不存在,是否返回默认的sp_check检查文档设置
    :return: sp检查列表,没有则为None
    """

    if img_recognize_file_name is None:
        file_name = "sp_check"
    else:
        file_name = os.path.join("img_rcg_reaction_sp_check", str(img_recognize_file_name))

    path = os.path.join(root_path_0, "program_parameter_presets", file_name + ".txt")

    if os.path.exists(path):
        file_read = read_presets(file_name, is_program_presets=True)
        sp_check_list = remove_enter_and_space_and_make_battle_list(file_read, return_int_list=True, list_lenth=3)
        return sp_check_list
    else:
        if default_return:
            file_read = read_presets("sp_check", is_program_presets=True)
            sp_check_list = remove_enter_and_space_and_make_battle_list(file_read, return_int_list=True, list_lenth=3)
            return sp_check_list
        else:
            return None
