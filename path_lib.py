import os
from pathlib import Path
# 所有识图文件路径字典


def get_root_path():
    """返回该py文件上一级的路径，生成exe后，返回exe所在文件夹的路径"""
    my_path = Path(__file__).resolve()  # 该.py所在目录
    if os.path.exists(my_path.parent.parent):
        return my_path.parent.parent
    else:
        print("路径错误")


root_path = get_root_path()

resource_path = {
    # 文件夹路径
    "root_path": root_path,
    "score_attack": os.path.join(root_path, "score_attack"),
    # 基本识图模版路径
    "start_action": os.path.join(root_path, "resource", "start_action.png"),
    "change_team": os.path.join(root_path, "resource", "change_team.png"),
    "exit": os.path.join(root_path, "resource", "exit.png"),
    "battle_result": os.path.join(root_path, "resource", "battle_result.png"),  # 战斗奖励结算
    "od_0": os.path.join(root_path, "resource", "od_0.png"),
    "od_1": os.path.join(root_path, "resource", "od_1.png"),
    "od_2": os.path.join(root_path, "resource", "od_2.png"),
    "od_3": os.path.join(root_path, "resource", "od_3.png"),
    "battle_failed": os.path.join(root_path, "resource", "battle_failed.png"),  # 识别到该模版认为战斗已经失败
    "battle_failed_1": os.path.join(root_path, "resource", "battle_failed_1.png"),  # 自定义失败模版
    "battle_failed_5": os.path.join(root_path, "resource", "battle_failed_5.png"),  # 遭遇战失败模版
    "battle_failed_9": os.path.join(root_path, "resource", "battle_failed_1.png"),  # 异时层失败模版
    # 预设文件路径
    "start_mode": os.path.join(root_path, "program_parameter_presets", "start_mode.txt"),
    "sp_check": os.path.join(root_path, "program_parameter_presets", "sp_check.txt"),
    "od_useful_level": os.path.join(root_path, "program_parameter_presets", "od_useful_level.txt"),
}

number_rear_template_path_list = [  # 识图数字模版的地址列表必须10个数字一组,并按顺序排列
    os.path.join(root_path, "resource", "number_rear_model", "0_rear_model.png"),
    os.path.join(root_path, "resource", "number_rear_model", "1_rear_model.png"),
    os.path.join(root_path, "resource", "number_rear_model", "2_rear_model.png"),
    os.path.join(root_path, "resource", "number_rear_model", "3_rear_model.png"),
    os.path.join(root_path, "resource", "number_rear_model", "4_rear_model.png"),
    os.path.join(root_path, "resource", "number_rear_model", "5_rear_model.png"),
    os.path.join(root_path, "resource", "number_rear_model", "6_rear_model.png"),
    os.path.join(root_path, "resource", "number_rear_model", "7_rear_model.png"),
    os.path.join(root_path, "resource", "number_rear_model", "8_rear_model.png"),
    os.path.join(root_path, "resource", "number_rear_model", "9_rear_model.png"),
    os.path.join(root_path, "resource", "number_rear_model", "0_rear_model_b.png"),
    os.path.join(root_path, "resource", "number_rear_model", "1_rear_model_b.png"),
    os.path.join(root_path, "resource", "number_rear_model", "2_rear_model_b.png"),
    os.path.join(root_path, "resource", "number_rear_model", "3_rear_model_b.png"),
    os.path.join(root_path, "resource", "number_rear_model", "4_rear_model_b.png"),
    os.path.join(root_path, "resource", "number_rear_model", "5_rear_model_b.png"),
    os.path.join(root_path, "resource", "number_rear_model", "6_rear_model_b.png"),
    os.path.join(root_path, "resource", "number_rear_model", "7_rear_model_b.png"),
    os.path.join(root_path, "resource", "number_rear_model", "8_rear_model_b.png"),
    os.path.join(root_path, "resource", "number_rear_model", "9_rear_model_b.png")
]

number_front_template_path_list = [  # 识图数字模版的地址列表必须10个数字一组,并按顺序排列
    os.path.join(root_path, "resource", "number_front_model", "0_front_model.png"),
    os.path.join(root_path, "resource", "number_front_model", "1_front_model.png"),
    os.path.join(root_path, "resource", "number_front_model", "2_front_model.png"),
    os.path.join(root_path, "resource", "number_front_model", "3_front_model.png"),
    os.path.join(root_path, "resource", "number_front_model", "4_front_model.png"),
    os.path.join(root_path, "resource", "number_front_model", "5_front_model.png"),
    os.path.join(root_path, "resource", "number_front_model", "6_front_model.png"),
    os.path.join(root_path, "resource", "number_front_model", "7_front_model.png"),
    os.path.join(root_path, "resource", "number_front_model", "8_front_model.png"),
    os.path.join(root_path, "resource", "number_front_model", "9_front_model.png"),
    os.path.join(root_path, "resource", "number_front_model", "0_front_model_b.png"),
    os.path.join(root_path, "resource", "number_front_model", "1_front_model_b.png"),
    os.path.join(root_path, "resource", "number_front_model", "2_front_model_b.png"),
    os.path.join(root_path, "resource", "number_front_model", "3_front_model_b.png"),
    os.path.join(root_path, "resource", "number_front_model", "4_front_model_b.png"),
    os.path.join(root_path, "resource", "number_front_model", "5_front_model_b.png"),
    os.path.join(root_path, "resource", "number_front_model", "6_front_model_b.png"),
    os.path.join(root_path, "resource", "number_front_model", "7_front_model_b.png"),
    os.path.join(root_path, "resource", "number_front_model", "8_front_model_b.png"),
    os.path.join(root_path, "resource", "number_front_model", "9_front_model_b.png")
]
