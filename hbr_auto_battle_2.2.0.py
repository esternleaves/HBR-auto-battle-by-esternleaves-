import os
import time
import threading
import numpy as np
from tkinter import *
from time import sleep
from keyboard import press_and_release
from mouse import hbr_left_click
from global_data import ppp, search_range, awaken_hbr_window, click_point, hbr_get_handle, get_time_str
from path_lib import resource_path
from presets_read import get_preset_path, get_sp_check_list, output_battle_list, read_file, save_file
from screenshot_match import extra_mode_101, screenshot_score_attack, save_enemy_label, use_od, update_battle_failed_rcg
from screenshot_match import get_start_flag, defalult_recognition, score_attack_result_recognition, rcg_daily_rewards
from screenshot_match import rcg_battle_result, is_likely_start_and_is_powerful_enemy, seraph_skirmish_sim_recognize
from sp_recognize import get_sp_through_initial_position
from action_in_battle_one_turn import action_in_battle_one_turn, clear_skill_use, press_key, press_key_list, change_team, auto_if_skill_could_not_use

ui_range = [700, 0, 1650, 500]  # 窗口范围[左上角x,左上角y,右下角x,右下角y]
ui_er = [search_range["window_size"][2] - ui_range[0], 0, ui_range[2] - ui_range[0], ui_range[3] - ui_range[1]]
ui_ot = [0, 0, search_range["window_size"][2] - ui_range[0], ui_range[3] - ui_range[1]]  # 被hbr窗口遮挡的部分
py_file_name = ((os.path.abspath(__file__)).split('\\')[-1]).replace('.py', '')


def default_place(item, place_range: list, default_interval: int = 6):
    """组件默认的place方法"""
    item.place(x=int(place_range[0] + 0.5 * default_interval), y=int(place_range[1] + 0.5 * default_interval),
               width=int(place_range[2] - place_range[0] - default_interval),
               height=int(place_range[3] - place_range[1] - default_interval), anchor=NW)


def grid_range_in_window(grid_list: list, range_in_window: list, rows=100, columns=100) -> list:
    """range_in_window窗口内执行grid()的区域,返回相对窗口自身的range,分了100*100"""
    width, height = (range_in_window[2] - range_in_window[0]) / rows, (range_in_window[3] - range_in_window[1]) / columns
    return [range_in_window[0] + grid_list[0] * width, range_in_window[1] + grid_list[1] * height,
            range_in_window[0] + grid_list[2] * width, range_in_window[1] + grid_list[3] * height]


def expose_range_grid(item, grid_list: list, default_interval=4):
    """不在hbr窗口遮挡范围内的grid()"""
    default_place(item, grid_range_in_window(grid_list, ui_er), default_interval=default_interval)


def other_grid(item, grid_list: list, default_interval=6):
    """在hbr窗口遮挡范围内的grid()"""
    default_place(item, grid_range_in_window(grid_list, ui_ot), default_interval=default_interval)


def gbr(number, rows=10, columns=3) -> list:
    """快捷按钮的简易grid排布"""
    row, column = number // columns, number % columns
    place_range = grid_range_in_window([0, 17, 33, 99],  # 快捷排布区
                                       [0, 0, search_range["window_size"][2] - ui_range[0], ui_range[3] - ui_range[1]])
    width, height = (place_range[2]-place_range[0])/columns, (place_range[3]-place_range[1])/rows
    return [int(place_range[0] + width * column), int(place_range[1] + height * row),
            int(place_range[0] + width * column + width), int(place_range[1] + height * row + height)]


class Application(Frame):
    """hbr自动战斗脚本的ui"""
    root = Tk()

    root.title(py_file_name + " (使用时请将游戏界面设为视窗1280*720,屏幕缩放为100%)")
    ui_windows_range = ui_range  # 窗口范围的屏幕坐标, [左上X, 左上Y,右下X, 右下Y]
    exposure_x_range = [search_range["window_size"][2], ui_windows_range[2]]  # 暴露在hbr窗口外的部分
    root.geometry(str(ui_windows_range[2] - ui_windows_range[0]) + "x" + str(ui_windows_range[3] - ui_windows_range[1])
                  + "+" + str(ui_windows_range[0]) + "+" + str(ui_windows_range[1]))
    root.resizable(False, False)

    # 固定读取
    file_sp_check_list_path = resource_path["sp_check"]
    file_start_mode = resource_path["start_mode"]
    file_od_useful_level = resource_path["od_useful_level"]
    is_test = ppp["is_test"]
    search_frequency = ppp["search_frequency"]
    recognize_button_circle = ppp["recognize_button_circle"]
    match_tolerance_special_1 = ppp["match_tolerance_special_1"]
    action_time_limit = ppp["action_time_limit"]
    click_od_time_before_sp_check = ppp["click_od_time_before_sp_check"]

    def __init__(self, master=root):
        super().__init__(master)
        self.master = master
        self.pack()
        self.root.bind('<Control-Alt-c>', lambda event: self.hbr_auto_battle_stop)
        self.root.protocol("WM_DELETE_WINDOW", self._quit)  # 终止线程再关窗口
        # 日志打印区
        self.scrollbar_log = Scrollbar(self.master, orient="vertical")
        self.text_log = Text(self.master, yscrollcommand=self.scrollbar_log.set, font=("Light", 14))
        self.scrollbar_log.config(command=self.text_log.yview)
        expose_range_grid(self.text_log, [1, 14, 94, 99], default_interval=0)
        expose_range_grid(self.scrollbar_log, [94, 14, 100, 99], default_interval=0)
        # 重开区-sp检查设置区
        self.if_pause_when_all_passed_var = IntVar()
        self.tip_sp_check_list = Label(self.master, text="sp检查列表", font=("arial", 11))
        self.if_pause_when_all_check_passed = Checkbutton(self.master, variable=self.if_pause_when_all_passed_var, text="sp检查内容\n全通过后暂停")
        self.scrollbar_sp_check_list = Scrollbar(self.master, orient="vertical")
        self.text_sp_check_list = Text(self.master, yscrollcommand=self.scrollbar_sp_check_list.set, font=("arial", 11))
        self.scrollbar_sp_check_list.config(command=self.text_sp_check_list.yview)
        other_grid(self.tip_sp_check_list, [82, 42, 98, 47], default_interval=0)
        other_grid(self.if_pause_when_all_check_passed, [82, 46, 99, 54], default_interval=0)
        other_grid(self.text_sp_check_list, [82, 54, 97, 99], default_interval=0)
        other_grid(self.scrollbar_sp_check_list, [82, 54, 97, 99], default_interval=0)
        # 重开区
        self.action_when_wrong_var = IntVar()
        self.battle_failed_tem_number_var = IntVar()
        self.if_full_against_powerful_enemy_var = IntVar()
        self.if_full_against_powerful_enemy_var.set(1)
        self.od_useful_level_entry = Entry(self.master)
        self.od_useful_level: int = 1
        self.choose_action_when_wrong(grid_range_in_window([81, 8, 100, 41], ui_ot))
        # 操作区
        self.if_skip_plot_var = IntVar()
        self.if_skip_plot_checkbutton = Checkbutton(self.master, variable=self.if_skip_plot_var, text="等待行动时按\nctrl时跳剧情")
        self.save_all_button = Button(self.master, text="保存\n设定", command=self.save_all_presets, font=("arial", 13))
        self.if_pop = IntVar()  # 运行完后是否弹窗
        self.if_pop_when_complete = Checkbutton(self.master, variable=self.if_pop, text="结束弹窗", font=("arial", 10))
        self.tip_start_mode = Label(self.master, text="启动模式")
        self.entry_start_mode = Entry(self.master, font=("arial", 11))
        self.run_button = Button(self.master, text="运行\n程序", command=self.press_run_button, font=("arial", 13))
        self.run_customize_button = Button(self.master, text="默认设置", command=self.default_set, font=("arial", 10))
        self.stop_button = Button(self.master, text="停止", command=self.hbr_auto_battle_stop)
        self.cuntinue_button = Button(self.master, text="继续运行", command=self.press_continue_button)
        other_grid(self.if_skip_plot_checkbutton, [82, 0, 99, 8])
        expose_range_grid(self.save_all_button, [0, 0, 25, 14])
        expose_range_grid(self.if_pop_when_complete, [25, 0, 50, 4])
        expose_range_grid(self.tip_start_mode, [25, 4, 41, 8])
        expose_range_grid(self.entry_start_mode, [41, 3.6, 50, 8.4])
        expose_range_grid(self.run_customize_button, [25, 8, 50, 14])
        expose_range_grid(self.run_button, [50, 0, 75, 14])
        expose_range_grid(self.stop_button, [75, 0, 100, 7])
        expose_range_grid(self.cuntinue_button, [75, 7, 100, 14])
        # 战斗方案选择/自定义打开区
        self.label_battle_list_edite = Label(self.master, text="正在编辑/0模式下待执行方案", font=("arial", 11), anchor="w")
        self.entry_battle_list_edite = Entry(self.master, font=("arial", 11))
        self.tip_battle_list_edite = Label(self.master, text=".txt", font=("arial", 11), anchor="w")
        self.button_battle_list_edite = Button(self.master, text="打开", font=("arial", 11), command=self.print_battle_list)
        other_grid(self.label_battle_list_edite, [0, 1, 33, 7])
        other_grid(self.entry_battle_list_edite, [33, 1, 68, 7])
        other_grid(self.tip_battle_list_edite, [67, 2, 72, 7])
        other_grid(self.button_battle_list_edite, [72, 0, 82, 8])
        # 快捷编辑
        self.scrollbar_battle_list_edite = Scrollbar(self.master, orient="vertical")
        self.text_battle_list_edite = Text(self.master, yscrollcommand=self.scrollbar_battle_list_edite.set, font=("arial", 17))
        self.scrollbar_battle_list_edite.config(command=self.text_battle_list_edite.yview)
        other_grid(self.text_battle_list_edite, [33, 8, 78, 99], default_interval=0)
        other_grid(self.scrollbar_battle_list_edite, [78, 8, 81, 99], default_interval=0)
        # 批量安放快捷按钮
        self.tip_battle_list_edite = Label(self.master, text="快捷编辑/快捷选择\n启动模式0战斗方案", font=("arial", 11), anchor="w")
        other_grid(self.tip_battle_list_edite, [0, 8, 33, 16])
        self.creat_convinient_component(gbr(0), "0", "0")
        self.creat_convinient_component(gbr(1), "1", "1")
        self.creat_convinient_component(gbr(2), "2", "2")
        self.creat_convinient_component(gbr(3), "3", "3")
        self.creat_convinient_component(gbr(4), "4", "4")
        self.creat_convinient_component(gbr(5), "5", "5")
        self.creat_convinient_component(gbr(6), "6", "6")
        self.creat_convinient_component(gbr(7), "7", "7")
        self.creat_convinient_component(gbr(8), "8", "8")
        self.creat_convinient_component(gbr(9), "9", "9")
        self.creat_convinient_component(gbr(10), "积分挑战", "score_attack", default_mode=1)
        self.creat_convinient_component(gbr(11), "钟楼", "bell_tower", default_mode=2)
        self.creat_convinient_component(gbr(12), "异时层", "divergence", default_mode=3, skip_plot=True)
        self.creat_convinient_component(gbr(13), "炽天使\n遭遇战", "seraph_skirmish_sim_1f")
        self.creat_convinient_component(gbr(15), "连续战斗1", "continuous_1", default_mode=4)
        self.creat_convinient_component(gbr(16), "连续战斗2", "continuous_2", default_mode=4)
        self.creat_convinient_component(gbr(17), "连续战斗3", "continuous_3", default_mode=4)
        self.creat_convinient_component(gbr(18), "连续战斗4", "continuous_4", default_mode=4)
        self.creat_convinient_component(gbr(19), "连续战斗\n精英敌人1", "continuous_powerful_enemy_1", default_mode=4)
        self.creat_convinient_component(gbr(20), "连续战斗\n精英敌人2", "continuous_powerful_enemy_2", default_mode=4)
        # 其他功能区
        self.tip_other = Label(self.master, text="其他功能", font=("Light", 12))
        self.entry_divergence = Entry(self.master, font=("arial", 11))
        self.tip_divergence = Label(self.master, text="异时层编号-梦泪层数\n-梦泪使用次数限制", font=("Light", 10))
        default_place(self.tip_other, gbr(21))
        self.edit_note(gbr(23))
        self.sp_check_test(gbr(24))
        self.screenshot_score_attack_label(gbr(25))
        self.shot_enemy_label(gbr(26))
        default_place(self.entry_divergence, gbr(29))
        default_place(self.tip_divergence, [gbr(27)[0], gbr(27)[1], gbr(28)[2], gbr(28)[3]])
        # 异时层数据
        self.ability_up_limit: int = 0  # 异时层梦泪使用限制次数
        self.divergence_enemy_number: int = 1  # 异时层敌人选择,从左到右分别为1,2,3....
        self.ability_up_number: int = 0  # 异时层梦泪使用层数
        # 暂停前残留数据
        self.un_executed_battle_list_all_teams = None
        self.un_executed_inherited_order_of_stations = None
        self.un_executed_inherited_turn = 0
        # 函数运行参量
        self.hbr_handle = None
        self.battle_list_all_teams = None
        self.start_mode = 0
        self.inherited_order_of_stations = None
        self.sp_check_list = None
        self.inherited_turn = 0
        self.if_skip_plot = False
        self.action_flag_when_wrong: int = 0
        # 初始化默认值,线程停止符
        self.initialize()
        self.run_thread_flag: bool = True

    def save_all_presets(self):
        """保存全部修改内容到txt文档和程序, 运行前也执行一次"""
        # 保存sp_check_list,函数里不加[:-1]每次会多保存一个换行回车,用久了会爆
        save_file(self.file_sp_check_list_path, self.text_sp_check_list.get(1.0, END)[:-1])
        self.sp_check_list = get_sp_check_list()
        # 保存start_mode
        save_file(self.file_start_mode, self.entry_start_mode.get())
        self.start_mode = int(self.entry_start_mode.get())
        # 根据entry_battle_list_edite中的文件名保存text_battle_list_edite中的battle_list
        file_name = self.entry_battle_list_edite.get()
        save_text = self.text_battle_list_edite.get(1.0, END)[:-1]
        if file_name in ["editable_note"]:  # 自定义提示文本
            save_file(get_preset_path(str(file_name), True), save_text)
        else:
            save_file(get_preset_path(str(file_name)), save_text)
        # 异时层参数
        divergence_set = np.array(self.entry_divergence.get().split("-"), int)
        self.divergence_enemy_number = divergence_set[0]  # 异时层梦泪使用限制次数
        self.ability_up_number = divergence_set[1]  # 异时层敌人选择,从左到右分别为1,2,3....
        self.ability_up_limit = divergence_set[2]  # 异时层梦泪使用层数
        # 是否跳剧情,sp检测全过是否暂停,技能不可用时如何行动
        self.if_skip_plot = self.if_skip_plot_var.get()
        self.if_pause_when_all_check_passed = self.if_pause_when_all_passed_var.get()
        self.action_flag_when_wrong = self.action_when_wrong_var.get()
        # 自动开od的起用等级
        self.od_useful_level = int(self.od_useful_level_entry.get())
        save_file(self.file_od_useful_level, str(self.od_useful_level))
        # 更新战斗失败的识图模版
        failed_tem_number = self.battle_failed_tem_number_var.get()
        if self.start_mode == 3:
            update_battle_failed_rcg(9)  # 异时层失败识图模版设置为game_over
        elif self.start_mode == 5:
            update_battle_failed_rcg(5)  # 遭遇战失败识图
        else:
            update_battle_failed_rcg(failed_tem_number)
        # 打印时间
        self.log_print(get_time_str())
        self.log_print("已成功保存全部设置")

    def default_set(self):
        """默认设置"""
        self.save_all_presets()
        if self.start_mode == 3:
            self.if_skip_plot_var.set(1)    # 异时层模式跳剧情
            update_battle_failed_rcg(9)  # 异时层失败识图模版设置为game_over
        elif self.start_mode == 5:
            update_battle_failed_rcg(5)  # 遭遇战失败识图
        else:
            if self.start_mode == 4:
                if self.action_flag_when_wrong == 0:
                    self.action_when_wrong_var.set(4)  # 道中模式sp不足默认普攻空过一回合
                    self.action_flag_when_wrong = self.action_when_wrong_var.get()
            else:
                if self.action_flag_when_wrong == 4:
                    self.action_when_wrong_var.set(0)  # 道中模式sp不足默认普攻空过一回合
                    self.action_flag_when_wrong = self.action_when_wrong_var.get()

    def creat_convinient_component(self,
                                   raw_range,
                                   button_text: str,
                                   file_name: str,
                                   default_mode=0,
                                   skip_plot: bool = False):
        """
        批量安放战斗列表快捷选择按钮
        :param raw_range: 按钮范围[左上角x,左上角y,右下角x,右下角y]
        :param button_text: 按钮文本
        :param file_name: 战斗预设对应的txt文件名称
        :param default_mode: 选择方案默认的start_mode
        :param skip_plot: 选择方案默认是否跳过剧情
        """
        def cb_press():
            self.update_entry(self.entry_battle_list_edite, file_name)
            self.print_battle_list()
            if default_mode == 0:
                self.update_entry(self.entry_start_mode, "0")
            self.if_skip_plot_var.set(skip_plot)
        cb = Button(self.master, text=button_text, command=cb_press)
        default_place(cb, raw_range)

    # 其他模式功能区
    def shot_enemy_label(self, range_0):
        """截图敌人名字列表"""
        def save_label():
            save_enemy_label()
            self.log_print("截图成功,请到resource/enemy_label-battle_preset中查看标签并重命名,系统在模式5下识别到该敌人标签后,"
                           "会执行battle_presets中文件‘标签名.txt’内的预设方案,若没有对应预设文件,则执行0.txt文件的方案")
        screenshot_button = Button(self.master, text="截图\n敌人标签", command=save_label)
        default_place(screenshot_button, range_0)

    def edit_note(self, range_0):
        """编辑自定义提示文档,提示方案的作用"""
        def edite_tip_note():
            self.update_entry(self.entry_battle_list_edite, "editable_note")
            self.print_program_preset("editable_note", True)
        screenshot_button = Button(self.master, text="编辑\n提示文本", command=edite_tip_note)
        default_place(screenshot_button, range_0)

    def screenshot_score_attack_label(self, range_0):
        """截图打分出分界面识图标签"""
        def shot():
            if handle := hbr_get_handle():
                self.hbr_handle = handle
                awaken_hbr_window(self.hbr_handle)
                extra_mode_101()
                self.log_print("打分识图标签截图完毕,请到exe文件同一目录里查看,注意将主c的mvp标签命名为screenshot_score_attack.png"
                               "并替换resource中的原文件")
            else:
                self.log_print("没有找到hbr的steam窗口")
        screenshot_button = Button(self.master, text="截图打分\n识图标签", command=shot)
        default_place(screenshot_button, range_0)

    def sp_check_test(self, range_0):
        """sp检查测试"""
        def check_test():
            if handle := hbr_get_handle():
                awaken_hbr_window(handle)
                for order in range(1, 7):
                    self.log_print("从左到右第" + str(order) + "位角色的sp为" + str(get_sp_through_initial_position(order)))
                self.pop_window()
            else:
                self.log_print("没有找到hbr的steam窗口")
        sp_check_test_button = Button(self.master, text="测试\nsp识别", command=check_test)
        default_place(sp_check_test_button, range_0)

    def choose_action_when_wrong(self, range_0):
        action_tip = Label(self.master, text="技能不可用时:", anchor="w")
        action_0 = Radiobutton(self.master, text="重开(0/4模式暂停)", anchor="w", variable=self.action_when_wrong_var, value=0)
        restart_tip = Label(self.master, text="重开识别模版:", anchor="w")
        restart_1 = Radiobutton(self.master, text="默认", anchor="w", variable=self.battle_failed_tem_number_var, value=0)
        restart_2 = Radiobutton(self.master, text="自定义(待添加)", anchor="w", variable=self.battle_failed_tem_number_var, value=1)
        action_1 = Radiobutton(self.master, text="暂停(所有模式)", anchor="w", variable=self.action_when_wrong_var, value=1)
        action_2 = Radiobutton(self.master, text="全员普攻至轴可用", anchor="w", variable=self.action_when_wrong_var,value=4)
        action_3 = Radiobutton(self.master, text="auto-normal", anchor="w", variable=self.action_when_wrong_var, value=2)
        action_3_1 = Checkbutton(self.master, text="精英时auto full", anchor="w", variable=self.if_full_against_powerful_enemy_var)
        action_4 = Radiobutton(self.master, text="auto-full", anchor="w", variable=self.action_when_wrong_var, value=3)
        action_tip_2 = Label(self.master, text="道中od起用等级", anchor="w")
        columns = 11
        default_place(action_tip, grid_range_in_window([0, 0, 1, 1], range_0, rows=1, columns=columns), default_interval=0)
        default_place(action_0, grid_range_in_window([0, 1, 1, 2], range_0, rows=1, columns=columns), default_interval=0)
        default_place(restart_tip, grid_range_in_window([0.1, 2, 1, 3], range_0, rows=1, columns=columns), default_interval=0)
        default_place(restart_1, grid_range_in_window([0.1, 3, 1, 4], range_0, rows=1, columns=columns), default_interval=0)
        default_place(restart_2, grid_range_in_window([0.1, 4, 1, 5], range_0, rows=1, columns=columns), default_interval=0)
        default_place(action_1, grid_range_in_window([0, 5, 1, 6], range_0, rows=1, columns=columns), default_interval=0)
        default_place(action_2, grid_range_in_window([0, 6, 1, 7], range_0, rows=1, columns=columns),default_interval=0)
        default_place(action_3, grid_range_in_window([0, 7, 1, 8], range_0, rows=1, columns=columns), default_interval=0)
        default_place(action_3_1, grid_range_in_window([0.1, 8, 1, 9], range_0, rows=1, columns=columns), default_interval=0)
        default_place(action_4, grid_range_in_window([0, 9, 1, 10], range_0, rows=1, columns=columns), default_interval=0)
        default_place(action_tip_2, grid_range_in_window([0, 10, 0.82, 11], range_0, rows=1, columns=columns), default_interval=0)
        default_place(self.od_useful_level_entry, grid_range_in_window([0.82, 10, 1, 11], range_0, rows=1, columns=columns), default_interval=0)

    # 读取文件和初始化
    def print_battle_list(self):
        """打开txt文件并在text_battle_list_edite中打印其内容"""
        file_path = get_preset_path(self.entry_battle_list_edite.get())
        if os.path.exists(file_path):
            battle_list_text = read_file(file_path)
            self.update_text(self.text_battle_list_edite, battle_list_text)
        else:
            self.text_battle_list_edite.delete(1.0, END)
            self.log_print("txt文件名有误\n如要创建新预设,可直接在文本框内编辑并按'保存设定'按钮")

    def print_program_preset(self, file_name: str, is_edite: bool = False):
        """
        打印系统预设文档
        :param file_name: 文件名,不用带.txt
        :param is_edite: 是在文本框内编辑还是打印在日志栏内
        :return: None
        """
        preset_path = os.path.join(resource_path["root_path"], "program_parameter_presets", file_name + ".txt")
        preset_note = read_file(preset_path, open_encoding='utf-8')
        if is_edite:
            self.update_text(self.text_battle_list_edite, preset_note)
        else:
            self.log_print(preset_note)

    def initialize(self):
        """初始化时,打印sp_check.txt和start_mode.txt中的全部内容到对应文本框中"""
        # sp_check.txt
        file_sp_check_list = read_file(self.file_sp_check_list_path)
        self.update_text(self.text_sp_check_list, file_sp_check_list)
        # start_mode.txt
        start_mode_read = read_file(self.file_start_mode)
        self.update_entry(self.entry_start_mode, start_mode_read)
        # 默认战斗方案"0.txt"的战斗列表
        file_battle_list = read_file(get_preset_path("0"))
        self.update_text(self.text_battle_list_edite, file_battle_list)
        # 默认战斗方案"0.txt"
        self.update_entry(self.entry_battle_list_edite, "0")
        # 默认道中od使用
        od_useful_level_read = read_file(self.file_od_useful_level)
        self.od_useful_level_entry.insert(0, od_useful_level_read)
        # 异时层初始
        self.entry_divergence.insert(0, string="1-0-1")
        # 提示文本
        self.print_mode_and_editable_tips()

    def print_mode_and_editable_tips(self):
        self.log_print("模式1打分.2钟楼.3异时层.4道中(轮流调用连续战斗1234方案,遇精英轮流调用精英方案12).5遭遇战")
        self.print_program_preset("editable_note")

    def update_un_executed_data(self, list1=None, list2=None, int3=0):
        self.un_executed_battle_list_all_teams = list1
        self.un_executed_inherited_order_of_stations = list2
        self.un_executed_inherited_turn = int(int3)

    def update_run_tip(self):
        self.log_print("程序开始运行")
        if self.sp_check_list:
            self.log_print("本次运行sp检查列表为:" + str(self.sp_check_list) + ".具体检查内容为:")
            for i in range(len(self.sp_check_list)):
                self.log_print("第" + str(self.sp_check_list[i][0]) + "动时,进场编队中从左到右第" + str(self.sp_check_list[i][1])
                               + "个角色的sp是否为" + str(self.sp_check_list[i][2]) + ".")
        if self.if_pause_when_all_check_passed:
            self.log_print("本次运行通过所有sp检查后暂停")
        if self.start_mode == 0:
            self.log_print("运行一般模式")
        elif self.start_mode == 1:
            self.log_print("运行无限打分循环")
        elif self.start_mode == 2:
            self.log_print("运行无限钟楼循环")
        elif self.start_mode == 3:
            self.log_print("运行无限异时层循环,将与异时层第" + str(self.divergence_enemy_number) + "个敌人战斗,使用" +
                           str(self.ability_up_number) + "层梦泪,最多使用" + str(self.ability_up_limit) + "次")
        elif self.start_mode == 4:
            self.log_print("运行道中模式,若选择技能不可用时重开,系统会自动切换为暂停,避免浪费票,其他选项不受影响")
        elif self.start_mode == 5:
            self.log_print("运行遭遇战模式,务必按说明文档内容编辑好识图模版和对应战斗方案")

    def press_run_button(self):
        """默认运行按钮按下"""
        self.save_all_presets()
        self.update_run_tip()
        self.update_battle_list_by_start_mode()
        self.inherited_order_of_stations = None
        self.inherited_turn = 0
        threading.Thread(target=self.run_thread_main).start()

    def press_continue_button(self):
        """按下继续运行按钮"""
        self.save_all_presets()
        self.update_run_tip()
        if self.un_executed_battle_list_all_teams:  # 有暂停前残留列表继续执行
            self.battle_list_all_teams = self.un_executed_battle_list_all_teams
            self.inherited_order_of_stations = self.un_executed_inherited_order_of_stations
            self.inherited_turn = int(self.un_executed_inherited_turn)
            threading.Thread(target=self.run_thread_main).start()
        else:
            self.log_print("没有暂停前的数据")

    def run_thread_main(self):
        """运行或暂停按钮按下的统一线程函数"""
        if handle := hbr_get_handle():
            self.hbr_handle = handle
            awaken_hbr_window(handle)
            self.run_thread_flag: bool = True
            self.update_un_executed_data()  # 线程启动后清空之前的暂停残留
            if self.start_mode:
                sleep(1)
            result = self.hbr_auto_battle_ui_main(self.start_mode)
            self.log_print(get_time_str())
            if result is True:
                self.log_print("正常完成本轮运行")
            elif result == "pause":
                self.log_print("程序暂停,按'继续运行'按钮结束暂停")
            elif result == "stop":
                self.log_print("程序已停止")
            else:
                self.log_print("程序错误结束")
            self.pop_window()
            self.print_mode_and_editable_tips()
        else:
            self.log_print("没有找到hbr的steam窗口")

    def hbr_auto_battle_ui_main(self, start_mode: int):
        """主操作循环"""
        count = [0, 0, 0]  # 计数
        if self.start_mode in [4]:  # 等道中开战
            self.enter_battle_in_special_mode(start_mode, count, if_complete=True)
        elif self.start_mode == 5:
            count[2] = 5  # 5次刷新
        while True:  # 用于正常结束一场战斗后的重开
            self.test_log_print(str(self.battle_list_all_teams))
            battle_list = self.battle_list_all_teams[:]  # 浅拷贝
            if self.inherited_order_of_stations:
                inherited_order_of_stations = self.inherited_order_of_stations
                self.inherited_order_of_stations = None
            else:
                inherited_order_of_stations = None
            if self.inherited_turn:
                inherited_turn = self.inherited_turn
                self.inherited_turn = 0
            else:
                inherited_turn = 0
            while (new_list := self.main_read_battle_list_to_battle(handle=self.hbr_handle,  # 用于一场战斗未正常结束的重开或换队
                                                                    battle_list_all_teams=battle_list,
                                                                    start_mode=start_mode,
                                                                    inherited_order_of_stations=inherited_order_of_stations,
                                                                    sp_check_list_in_battle=self.sp_check_list,
                                                                    if_skip_plot_main=self.if_skip_plot,
                                                                    inherited_turn=inherited_turn))[0]:
                # 一场战斗中途退出
                if not self.run_thread_flag:  # 线程退出点
                    return "stop"
                elif new_list[0] in ["change_team", "empty_over"]:  # 万一以后打分钟楼能换队了呢(空过也走这条路)
                    battle_list = new_list[1]
                    inherited_order_of_stations = new_list[2]
                    inherited_turn = new_list[3]
                elif new_list[0] in ["pause"]:
                    self.update_un_executed_data(new_list[1], new_list[2], new_list[3])
                    if new_list[0] == "pause":
                        return "pause"
                elif start_mode == 0:
                    break
                else:  # 启动模式1,2,3...重开
                    if_continue = self.enter_battle_in_special_mode(start_mode, count)  # 这里会在计数器为1时更新一次self.battle_list_all_teams
                    if not if_continue:  # 炽天使遭遇战打到最后一关,并正确选牌后停止等
                        return "stop"
                    battle_list = self.battle_list_all_teams[:]
                    inherited_order_of_stations = None
                    inherited_turn = 0
                self.test_log_print(str(new_list) + str(self.battle_list_all_teams))
            # 一场战斗正常结束,这里会在计数器为1时更新一次battle_list,避免从暂停开始打出问题
            if not self.run_thread_flag:  # 线程退出点
                return "stop"
            elif start_mode == 0:  # start_mode为0模式不需要结束战斗后无限循环
                break
            else:
                if start_mode == 1:
                    self.screenshot_score_attack_result(self.hbr_handle)  # 积分挑战出分截图保存
                if_continue = self.enter_battle_in_special_mode(start_mode, count, True)
                if not if_continue:  # 炽天使遭遇战打到最后一关,并正确选牌后停止等
                    return "stop"
        # 所有战斗全部结束
        if not self.run_thread_flag:  # 线程退出点
            return "stop"
        else:
            return True

    # 主函数
    def exit_battle(self, if_skip_plot=0) -> None:
        """识别到可以退出战斗时,退出战斗,并识图确认"""
        while not get_start_flag() is True:  # 万一要多次换队才能退战斗
            if not self.run_thread_flag:  # 线程退出点
                return None
            elif self.sleep_until_could_action(if_skip_plot, self.action_time_limit) is True:
                change_team()
            else:
                break  # 超时和线程停止
        while get_start_flag():  # 点过一轮还能搜索到按钮，说明没有成功退出
            press_key_list(["Esc", "Enter", "Esc"])
            sleep(self.search_frequency)

    def sleep_until_could_action(self, if_skip_plot=0, time_limit=45) -> bool:
        """
        检测到行动和退出按钮后开始行动,若没有检测到,search_frequency秒后再检测一次
        超出检测时限,认为角色已经被打死,默认时限45s,可在action_time_limit.txt中调
        有些时候需要等待时按下ctrl跳过剧情
        """
        search_flag_sleep: int = 0
        search_limit_sleep = int(time_limit / self.search_frequency)
        while True:
            start_flag = get_start_flag()
            if (self.run_thread_flag is False) or start_flag:  # 线程退出点
                return True
            elif (search_flag_sleep > search_limit_sleep) or (start_flag is False):  # 查找超时则False,默认为至少10s开不出od
                return False  # 查找超时同样认为角色在上一动敌方行动时被打死
            elif rcg_battle_result():  # 提前打死了,双重确认保证不出错,退战斗奖励结算写在后面
                sleep(self.search_frequency)
                if rcg_battle_result():  # 双重确认保证不出错
                    return True
            else:
                search_flag_sleep = search_flag_sleep + 1
                if if_skip_plot:  # 跳过剧情时限要长一点
                    press_key("Ctrl", press_time=self.search_frequency + 0.3, sleep_time=0.1)
                else:
                    sleep(self.search_frequency)

    def auto_mode(self, auto_full: bool = True, time_limit=45, if_skip_plot=0) -> bool:
        """发现技能不可用时,开启auto_full模式自动的战斗,auto_full为false则auto-normal"""
        t0 = time.time()
        while True:
            start_flag = get_start_flag()
            if not self.run_thread_flag:  # 线程退出点
                return True
            elif (time.time() - t0 > time_limit + 15) or (start_flag is False):  # auto稍微长一点
                return False  # 认为角色被打死了(超时依然)
            elif start_flag:
                auto_if_skill_could_not_use(self.hbr_handle, auto_full=auto_full)
                t0 = time.time()
                sleep(7)
            elif rcg_battle_result():  # 通过自动模式顺利结束战斗
                sleep(self.search_frequency)
                if rcg_battle_result():  # 双重确认保证不出错
                    if self.exit_battle_reward(time_limit=self.action_time_limit):
                        return True
            else:
                sleep(1)

    def exit_battle_reward(self, time_limit=65, if_skip_plot=0) -> bool:
        """退出战斗奖励结算画面,True代表正确退出"""
        t0 = time.time()
        while not rcg_battle_result():
            if not self.run_thread_flag:  # 线程退出点
                return True
            elif get_start_flag():  # 还能识别到下一动,说明没打死
                wrong_action_result = self.action_battle_error()
                if wrong_action_result == "restart":  # 按计划重开,self.action_battle_error中已经退战斗
                    return True
                elif wrong_action_result == "complete":  # 通过auto——normal/full正常结束战斗
                    return True
                else:  # if wrong_action_result is False:  # 停止
                    self.hbr_auto_battle_stop()
                    return False
            else:
                if time.time() - t0 > time_limit:  # 超时
                    return False
                elif if_skip_plot:  # 跳过剧情时限要长一点,异时层结算动画更长
                    press_key("Ctrl", press_time=self.search_frequency + 0.3, sleep_time=0.2)
                else:
                    sleep(self.search_frequency)
        while rcg_battle_result():
            press_and_release("Enter")  # 万一有技能升级,按两下
            sleep(1.5)
            press_and_release("Enter")
            sleep(2)
        return True

    def start_action(self, handle):
        """按下start action按钮"""
        hbr_left_click(handle, click_point["start_action"])  # 按一下行动按钮
        sleep(0.1)
        press_and_release("Enter")
        sleep(self.search_frequency)

    def main_read_battle_list_to_battle(self,
                                        handle,
                                        battle_list_all_teams: list,
                                        start_mode: int,
                                        inherited_order_of_stations=None,
                                        sp_check_list_in_battle: list = None,
                                        inherited_turn: int = 0,
                                        if_skip_plot_main=0) -> list:
        """
        单次战斗主函数,加载一整个battle_list列表并操作战斗,
        :param handle: hbr窗口句柄
        :param battle_list_all_teams: 全部队伍的战斗列表(3D list):一回合的行动是1D list,一队是2D list,全部队伍是3D list
        :param start_mode: 程序启动模式,基本模式为0
        :param inherited_order_of_stations: 需要继承的全部队伍的站位列表(2D list),一队为1D list,无输入会根据战斗列表自动生成默认
        :param sp_check_list_in_battle: 全部队伍的sp检查列表(3D list),一回合的行动是1D list,一队是二维列表
        :param inherited_turn: 暂停或换队前全部队伍已执行的行动数,用于暂停和换队后的sp检查模块
        :param if_skip_plot_main: 等待start action按钮亮起时是否间歇按Ctrl跳剧情
        :return: list 返回指令(str),仍可能需要执行的battle_list_all_teams(3D list),全部队伍的order_of_stations(2D list),已执行的turn数(int).
        返回指令指示战斗返回的后续操作.
        """
        def loop_if_action_failled(one_action, flag: bool = True) -> bool:
            """三个人不可能在search_frequency秒内放完技能,此时还能检测到行动和退出按钮,说明没有行动成功,重新行动"""
            result = True
            while get_start_flag():
                if not self.run_thread_flag:  # 线程退出点
                    return True
                else:
                    result = action_in_battle_one_turn(handle, one_action, order_of_stations_all_teams[0], flag)
                if not self.run_thread_flag:  # 线程退出点
                    return True
                elif result is False:
                    return False
                else:
                    self.start_action(handle)
            return result

        def use_od_before_action() -> bool:
            """如果前置od,先把od开了,一定时间内开不出od就是od槽没满,根据sp检测准备重开"""
            search_flag_od: int = 0
            search_limit_od = int(self.click_od_time_before_sp_check)
            while get_start_flag():
                press_key("o", sleep_time=0)
                sleep(1)  # 1s不能开完od，此时还能检测到行动和退出按钮,说明没有开到od,重新开
                if not self.run_thread_flag:  # 线程退出点
                    return True
                else:
                    search_flag_od = search_flag_od + 1
                    if search_flag_od > search_limit_od:  # 查找超时则False,默认为至少10s开不出od
                        return False

        def use_od_after_action(time_limit=45, flag: bool = True) -> bool:
            """如果后置od,一定时间没开出来就是角色被打死了
            超出检测时限,认为角色已经被打死,默认时限45s,可在action_time_limit.txt中调"""
            search_flag_od: int = 0
            search_limit = int(time_limit)
            while True:  # 在下一动可以行动前,一直点击od按钮
                start_flag = get_start_flag()
                if (not self.run_thread_flag) or start_flag:  # 线程退出点, 等到了下一回合
                    return True
                elif flag is False:
                    return True
                else:
                    search_flag_od = search_flag_od + 1
                    if (search_flag_od > search_limit) or (start_flag is False):  # 查找超时则False,默认为至少10s开不出od
                        return False
                    for i_click_od in range(6):  # 每秒一轮
                        press_key("o", press_time=0.1, sleep_time=0.05)

        def return_un_executed_list(turn_number, command_str: str = "pause") -> list:
            """换队返回未执行参数,切片返回未执行过的战斗列表,当前的角色站位,已执行的动数和换队指令,适配多队,也适用全员普攻空过"""
            if command_str == "change_team":
                change_team_left_list = battle_list_all_teams[1:] + [battle_list[turn_number + 1:]]  # 换队调到最后去,切掉换队指令
                return ["change_team", change_team_left_list,
                        order_of_stations_all_teams[1:] + order_of_stations_all_teams[:1], inherited_turn + turn_number]
            elif command_str == "empty_over":  # 全员普攻空过直至轴可用
                change_team_left_list = [battle_list[turn_number:]] + battle_list_all_teams[1:]  # 全员普攻空过不切掉本回合
                return ["empty_over", change_team_left_list, order_of_stations_all_teams, inherited_turn + turn_number]
            elif command_str == "pause_set":
                list_return = [battle_list[turn_number + 1:]] + battle_list_all_teams[1:]  # 切掉暂停指令的0列表
                return ["pause", list_return, order_of_stations_all_teams, inherited_turn + turn_number]
            else:  # "pause"默认暂停切片
                list_return = [battle_list[turn_number:]] + battle_list_all_teams[1:]
                return ["pause", list_return, order_of_stations_all_teams, inherited_turn + turn_number]

        # 预处理,根据battle_list_all_teams对多队站位列表,已执行动数列表的默认值初始化
        number_of_team = len(battle_list_all_teams)
        if_exit_battle_reward = False
        if battle_list_all_teams[0]:  # 确保非空,不然下一行会报错
            if all(x == 0 for x in (battle_list_all_teams[0])[-1:][0]):
                battle_list = (battle_list_all_teams[0])[:-1]
                if start_mode == 0:
                    if_exit_battle_reward = True
            else:
                battle_list = battle_list_all_teams[0]
        else:
            battle_list = battle_list_all_teams[0]
        if start_mode != 0:
            if_exit_battle_reward = self.if_exit_battle_reward_by_start_mode(start_mode)
        # 没有就初始化一下
        if not inherited_order_of_stations:
            order_of_stations_all_teams = [[1, 2, 3, 4, 5, 6]] * number_of_team
        else:
            order_of_stations_all_teams = inherited_order_of_stations  # 有需要继承的order_of_stations就继承
        if not sp_check_list_in_battle:  # 默认sp检查列表为空
            sp_check_list_in_battle = []
        if not inherited_turn:
            inherited_turn = 0

        # 逐回合根据子列表战斗
        action_flag: bool = True
        for turn in range(len(battle_list)):

            if all(x == 0 for x in battle_list[turn]):  # 暂停模块,伪暂停,返回暂停前未执行的list和行动列表
                return return_un_executed_list(turn, command_str="pause_set")  # 暂停截取

            if battle_list[turn][0] == 2:  # 换队模块,注意这里可能有剧情,正常等待可能会检测超时触发重开,适当延长检测时间
                self.sleep_until_could_action(if_skip_plot_main, self.action_time_limit + 10)
                change_team()
                return return_un_executed_list(turn, command_str="change_team")  # 换队截取

            # 等待start action按钮亮起并先开od,若查找超时,则认为角色在上一动敌方行动时被打死
            run_flag: bool = True
            if battle_list[turn][0] == 1:  # 需要先开od,不管怎么样,先把od开了,sp检测在先开od后
                run_flag = self.sleep_until_could_action(if_skip_plot_main, self.action_time_limit)
                if run_flag:
                    use_od_before_action()
            if run_flag:  # 正常回合等待
                run_flag = self.sleep_until_could_action(if_skip_plot_main, self.action_time_limit)

            if not self.run_thread_flag:  # 线程退出点
                return ["stop", None, None, 0]
            elif rcg_battle_result():  # 检测到战斗奖励结算,认为提前打死了敌人
                sleep(self.search_frequency)
                if rcg_battle_result():  # 双重确认保证不出错
                    if self.exit_battle_reward(time_limit=self.action_time_limit):
                        return [None, None, None, 0]
            elif run_flag is False:  # 认为被打死,退出函数准备重开
                wrong_action_result = self.action_battle_error()
                if wrong_action_result == "restart":  # 按计划重开
                    return self.output_list_by_start_mode_when_restart(start_mode)
                elif wrong_action_result == "complete":  # 通过auto——normal/full正常结束战斗
                    return [None, None, None, 0]
                else:  # 停止
                    self.log_print("怀疑角色被打死,请检查")
                    return ["stop", None, None, 0]

            # 检测sp模块
            if long := len(sp_check_list_in_battle):
                check_list_this_turn = []  # [[检查回合(首回合为1),角色1的进场编号,角色1正确的sp值],[回合,角色2......]]
                all_check_pass_flag: int = -1  # 标志最后要检测的回合
                for i_sp_check in range(long):  # 获得本回合的检查列表
                    if sp_check_list_in_battle[i_sp_check][0] - 1 == turn + inherited_turn:  # 第n动为battle_list[n-1]
                        check_list_this_turn.append(sp_check_list_in_battle[i_sp_check])
                    if sp_check_list_in_battle[i_sp_check][0] - 1 > all_check_pass_flag:
                        all_check_pass_flag = sp_check_list_in_battle[i_sp_check][0] - 1
                if long_this_turn := len(check_list_this_turn):  # 检查本回合的sp
                    check_flag: bool = True
                    if turn > 0:  # 后开od会残留技能使用的选择,如果检查的对象在前排,清空一下技能选择再检查sp,首回合不清空技能
                        if battle_list[turn - 1][0] == -1:
                            clear_skill_use(handle, order_of_stations_all_teams[0], check_list_this_turn)
                    for j_sp_check in range(long_this_turn):
                        sp = get_sp_through_initial_position(check_list_this_turn[j_sp_check][1],
                                                             order_of_stations_all_teams[0])
                        if sp != check_list_this_turn[j_sp_check][2]:
                            check_flag = False
                else:
                    check_flag = True
                if not check_flag:  # 代表检查sp出错,重开战斗
                    wrong_action_result = self.action_battle_error()
                    if wrong_action_result == "restart":  # 按计划重开
                        return self.output_list_by_start_mode_when_restart(start_mode)
                    elif wrong_action_result == "complete":  # 通过auto——normal/full正常结束战斗
                        return [None, None, None, 0]
                    else:  # 停止
                        self.log_print("sp检查错误,如果要继续运行,请删除该回合的sp检查列表,保存后按'继续运行'.")
                        return return_un_executed_list(turn, command_str="pause")
                if turn == all_check_pass_flag:
                    if self.if_pause_when_all_check_passed:  # 全部通过后是否暂停
                        return return_un_executed_list(turn, command_str="pause")

            # 正常行动部分,action_flag为false就是技能没有按照期望使用,接下来的回合都开auto模式
            if battle_list[turn][0] in [0, 1]:  # 不开od或先开od,前面已经开过
                action_flag = loop_if_action_failled(battle_list[turn], action_flag)
            elif battle_list[turn][0] == -1:  # 后开od
                action_flag = loop_if_action_failled(battle_list[turn], action_flag)
                sleep(4)  # 行动至少4秒
                result_od = use_od_after_action(time_limit=self.action_time_limit, flag=action_flag)
                if not result_od:  # 过长时间检测不到下一动,怀疑被打死
                    return self.output_list_by_start_mode_when_restart(start_mode)
            else:
                self.log_print("battle_list错误")
                return ["stop", None, None, 0]

            if action_flag is False:  # sp不够,执行错误时的行动
                self.log_print("sp不足以使用技能")
                wrong_action_result = self.action_battle_error()
                if wrong_action_result == "restart":  # 按计划重开
                    return self.output_list_by_start_mode_when_restart(start_mode)
                elif wrong_action_result == "complete":  # 通过auto——normal/full正常结束战斗
                    return [None, None, None, 0]
                elif wrong_action_result == "continue":  # 普攻空过直至接下来的轴可用
                    clear_skill_use(handle, order_of_stations_all_teams[0])
                    self.start_action(handle)
                    return return_un_executed_list(turn, command_str="empty_over")
                else:  # 停止
                    return ["stop", None, None, 0]

        if not self.run_thread_flag:  # 线程退出点
            return ["stop", None, None, 0]
        else:
            if if_exit_battle_reward:  # 退出游戏战斗奖励结算
                sleep(8)
                self.exit_battle_reward(self.action_time_limit, if_skip_plot=if_skip_plot_main)
            battle_list_left = battle_list_all_teams[1:] + [[]]  # 清空已执行
            if all(other_list == [] for other_list in battle_list_left):  # 全部执行完
                return [None, None, None, 0]
            else:
                return ["un_executed", battle_list_left, None, 0]

    # 退出、进入战斗部分
    def img_rcg_action(self,
                       img_target_list: list,
                       alternative_keyboard_action: list = None,
                       handle=None,
                       img_resource_sub_file_name: str = None,
                       search_sleep_time: float = 0.3,
                       wait_new_window_time: float = 1.4,
                       press_sleep_time: float = 0.4,
                       time_limit: int = 105) -> bool:
        """
        战斗外默认识图操作函数,用于通过键盘鼠标混合输入进行识图点击或识图键盘操作,如进入打分/钟楼/异时层
        :param img_target_list: 1D list, 需要识别的img文件名列表
        :param alternative_keyboard_action: 2D list,识图对应的按键,每一张图对应一个1D list,1D list为空采用鼠标点击
        :param handle: 采用鼠标点击时输入的句柄,如果没有,按屏幕绝对坐标点击, hbr窗口必须有句柄才能点的动
        :param img_resource_sub_file_name: 图片位于resource的哪个子文件夹下
        :param search_sleep_time: 识图等待时间
        :param wait_new_window_time: 识图成功,操作完毕后等待新的窗口弹出的时间
        :param press_sleep_time: 按键列表逐个按下的时间间隔
        :param time_limit: 识图过程允许的最长时间,单位s,超时自动退出
        :return: True/False代表是否执行正确
        """
        if button_number := len(img_target_list):
            if img_resource_sub_file_name:  # 如果图片位于resource的子文件夹下
                for num in range(len(img_target_list)):
                    img_target_list[num] = os.path.join(img_resource_sub_file_name, img_target_list[num])
            if not alternative_keyboard_action:
                alternative_keyboard_action = [[]] * len(img_target_list)
            t0 = time.time()
            while not defalult_recognition(img_target_list[button_number - 1]):
                if not self.run_thread_flag:  # 线程退出点
                    return True
                elif time.time() - t0 > time_limit:  # 超时,可能是断网之类或者跳了其他窗口导致找不到进入关卡的按钮
                    if rcg_daily_rewards():  # 有可能是每天凌晨一次的奖励结算界面弹出
                        sleep(search_sleep_time)
                        t0 = time.time()  # 重新设定超时时限
                    else:
                        return False  # 确实已超时
                else:
                    sleep(search_sleep_time)
                for j in range(button_number - 1):
                    if point_j := defalult_recognition(img_target_list[j]):
                        if alternative_keyboard_action[j]:  # 设置了对应按键
                            press_key_list(alternative_keyboard_action[j], press_sleep_time)
                        else:  # 未设置对应按键就鼠标点
                            sleep(press_sleep_time)  # 识到图了不等于你马上能点
                            hbr_left_click(handle, point_j)
                        sleep(wait_new_window_time)  # 等待窗口跳转
                    else:
                        sleep(search_sleep_time)
            while point_last := defalult_recognition(img_target_list[button_number - 1]):
                if not self.run_thread_flag:  # 线程退出点
                    return True
                elif alternative_keyboard_action[button_number - 1]:
                    press_key_list(alternative_keyboard_action[button_number - 1], press_sleep_time)
                else:
                    sleep(press_sleep_time)  # 识到图了不等于你马上能点
                    hbr_left_click(handle, point_last)
            return True
        else:
            return False

    def enter_bell_tower(self) -> bool:
        """进钟楼,["s", "Enter", "w"]中最后的"w"是为了防止前面的"Enter"没按下去"""
        return self.img_rcg_action(["exclamation_tip", "fight_bell_tower", "attack"],
                                   [["f"], ["Enter"], ["s", "Enter", "w"]],
                                   self.hbr_handle, img_resource_sub_file_name="enter_battle",
                                   search_sleep_time=self.recognize_button_circle)

    def enter_score_attack(self) -> bool:
        """进打分,["Enter","f"]防跳奖励弹窗界面,
        ["s", "Enter", "w"]中最后的"w"是为了防止前面的"Enter"没按下去"""
        return self.img_rcg_action(["exclamation_tip", "ok", "challenge_score_attack", "attack"],
                                   [["Enter", "f"], ["Enter"], ["s", "Enter"], ["s", "Enter", "w"]],
                                   self.hbr_handle, img_resource_sub_file_name="enter_battle",
                                   search_sleep_time=self.recognize_button_circle)

    def enter_divergence(self, enemy_number: int = 1, ability_up_leval: int = 0, ability_up_limit: int = 0) -> bool:
        """enemy_number异时层从左到右1,2,3...,ability_up_leval梦泪层数,ability_up_limit允许使用的梦泪次数,子列表空为鼠标点击"""
        if ability_up_limit > 0 and ability_up_leval:
            s_t = ["game_over", "strengthen_cultivate", "divergence_0", "divergence",
                   "challenge_divergence", "0_level", "determine", str(ability_up_leval) + "_level"]
            a_k_a = [["Enter"], [], [], ["d"] * enemy_number + ["Enter"] + ["a"] * enemy_number,
                     ["f", "Enter"], [], ["d"] * ability_up_leval + ["Enter"], ["w", "d", "Enter"]]
        else:  # sm飞机社,异时层挑战按钮比打分的挑战按钮字间距大
            s_t = ["game_over", "strengthen_cultivate", "divergence_0", "divergence", "challenge_divergence", "0_level"]
            a_k_a = [["Enter"], [], [], ["d"] * enemy_number + ["Enter"] + ["a"] * enemy_number,
                     ["f", "Enter"], ["w", "d", "Enter"]]
        return self.img_rcg_action(s_t, a_k_a, self.hbr_handle, img_resource_sub_file_name="enter_battle",
                                   search_sleep_time=self.recognize_button_circle)

    def enter_sss_battle(self) -> bool:
        """进遭遇战,["Enter","f"]防跳奖励弹窗界面,
        ["s", "Enter", "w"]中最后的"w"是为了防止前面的"Enter"没按下去"""
        return self.img_rcg_action(["exercise_start", "practice_mode", "ok", "attack"],
                                   [[], [], ["Enter"], ["s", "Enter", "w"]],
                                   self.hbr_handle, img_resource_sub_file_name="enter_battle",
                                   search_sleep_time=self.recognize_button_circle)

    def screenshot_score_attack_result(self, handle, time_limit=60) -> bool:
        """自动打分模式,识图截图出分并重开下一把"""
        sleep(10)  # 最后一动少说10s吧
        t0 = time.time()
        while not score_attack_result_recognition(match_tolerance=self.match_tolerance_special_1):
            if not self.run_thread_flag:  # 线程退出点
                return True
            elif time.time() - t0 > time_limit:  # 超时, 可能出错,也可能最后一回合直接被打死
                return False
            self.test_log_print("未识图成功", print_in_text=True)
            if get_start_flag():  # 由于幻惑混乱之类的没打死,还能检测到start_action按钮,直接重开
                self.exit_battle(self.if_skip_plot)
                return False
            else:
                press_and_release("Enter")
                sleep(2)
        while score_attack_result_recognition(match_tolerance=self.match_tolerance_special_1):
            self.test_log_print("识图成功,正在截图保存", print_in_text=True)
            screenshot_score_attack()
            sleep(0.5)
            press_and_release("Enter")
            sleep(1.5)
        return True

    def log_print(self, print_contents):
        self.text_log.insert(END, str(print_contents) + "\n")
        self.text_log.see(END)
        if self.is_test:  # 测试时打印在控制台
            print(print_contents)

    def test_log_print(self, print_contents, print_in_text=False):
        if self.is_test:
            print(print_contents)
            if print_in_text:
                self.log_print(print_contents)

    def update_entry(self, target_entry, update_text):
        target_entry.delete(0, END)
        target_entry.insert(0, string=str(update_text))

    def update_text(self, target_text, update_text):
        target_text.delete(1.0, END)
        target_text.insert(1.0, update_text)

    # 运行调用,关闭/弹出/维持窗口
    def pop_window(self):
        if self.if_pop.get():
            self.root.wm_attributes("-topmost", True)
            self.root.wm_attributes("-topmost", False)

    def hbr_auto_battle_stop(self):  # 停止线程
        self.run_thread_flag = False

    def hbr_auto_battle_run(self):  # 维持窗口
        self.root.mainloop()

    def _quit(self):
        def close_window():
            sleep(5)
            # self.root.destroy() 不加这一行窗口也会关闭,加了反而会无法正常结束线程关闭窗口
            self.root.quit()
        self.hbr_auto_battle_stop()
        threading.Thread(target=close_window).start()

    def wait_next_battle(self, count_number, time_limit=360) -> bool:  # 道中模式等待战斗,最大等待6分钟
        """道中模式4等待下一场战斗开始"""
        t0 = time.time()
        normal_enemy_flag: bool = True  # 默认遇到一般敌人 count_number[0] = count_number[0] + 1
        while True:
            if not self.run_thread_flag:
                return True
            elif time.time() - t0 > time_limit:
                self.battle_list_all_teams = output_battle_list("0")
                self.hbr_auto_battle_stop()
                self.log_print("等待战斗超时")
                return False
            else:
                is_likely_start_and_is_powerful_enemy_list = is_likely_start_and_is_powerful_enemy()
                if is_likely_start_and_is_powerful_enemy_list[0]:  # 战斗开始
                    use_od(self.od_useful_level)  # 用两次,免得没点出来
                    use_od(self.od_useful_level)
                    break
                elif is_likely_start_and_is_powerful_enemy_list[1]:  # 遇到精英了
                    normal_enemy_flag = False
                sleep(1.5)
        if normal_enemy_flag:
            self.action_flag_when_wrong = self.action_when_wrong_var.get()
            preset_name = "continuous_" + str((count_number[1] % 4) + 1)  # 轮流读取一般方案
            count_number[1] = count_number[1] + 1  # 遇敌普通时轮一遍4个方案选取
        else:
            if (self.action_flag_when_wrong == 2) and (self.if_full_against_powerful_enemy_var.get() == 1):
                self.action_flag_when_wrong = 3  # 精英敌人自动把auto normal改成auto full
            preset_name = "continuous_powerful_enemy_" + str(((count_number[0] - count_number[1]) % 2) + 1)
        self.battle_list_all_teams = output_battle_list(preset_name)
        self.test_log_print(preset_name + str(count_number))
        return True

    def wait_card_choose(self, time_limit=60):  # 道中模式等待战斗,最大等待6分钟
        """等待遭遇战选牌界面出现"""
        t0 = time.time()
        while True:
            if not self.run_thread_flag:
                return True
            elif defalult_recognition("auto_off_sss_battle", search_range["auto_off_sss_battle"]):
                sleep(self.search_frequency)
                return True
            elif time.time() - t0 > time_limit:
                self.battle_list_all_teams = output_battle_list("0")
                self.hbr_auto_battle_stop()
                self.log_print("选卡超时")
                return False
            sleep(self.search_frequency)

    def update_battle_list_by_start_mode(self):
        if self.start_mode == 1:
            self.battle_list_all_teams = output_battle_list("score_attack")
        elif self.start_mode == 2:
            self.battle_list_all_teams = output_battle_list("bell_tower")
        elif self.start_mode == 3:
            self.battle_list_all_teams = output_battle_list("divergence")
        elif self.start_mode == 4:
            self.battle_list_all_teams = output_battle_list("continuous_1")
        elif self.start_mode == 5:
            self.battle_list_all_teams = output_battle_list("seraph_skirmish_sim_1f")
        else:
            self.battle_list_all_teams = output_battle_list(str(self.entry_battle_list_edite.get()))

    def action_battle_error(self) -> str:
        """战斗识别错误(sp检查错误/战斗应该结束却还没有结束等)在不同设置和不同启动模式下如何行动"""
        if self.action_flag_when_wrong == 0:  # 重开
            if self.start_mode in [0, 4]:
                return "stop_or_pause"
            else:
                self.exit_battle(self.if_skip_plot)
                return "restart"  # 正常没凹出来重开
        elif self.action_flag_when_wrong == 1:  # 停
            return "stop_or_pause"
        elif self.action_flag_when_wrong == 4:  # 普攻直至轴可用
            return "continue"
        elif self.action_flag_when_wrong in [2, 3]:  # auto_normal/full
            result = self.auto_mode(bool(self.action_flag_when_wrong - 2), self.action_time_limit, self.if_skip_plot)
            if not result:  # 自动错误,停止
                return "stop_or_pause"
            else:
                return "complete"  # 通过auto模式正常结束战斗,此时已退出战斗奖励结算部分
        else:
            return "stop_or_pause"

    def if_exit_battle_reward_by_start_mode(self, start_mode: int) -> bool:
        """非0模式下是否要增加退出战斗奖励结算部分"""
        if start_mode in [1]:
            return False
        else:  # start_mode in [2, 3, 4, 5]:
            return True

    def output_list_by_start_mode_when_restart(self, start_mode: int) -> list:
        """各模式中途重开时的返回"""
        if start_mode == 0:
            return [None, None, None, 0]
        elif start_mode == 1:  # 重开打分
            return ["score_attack", None, None, 0]
        elif start_mode == 2:  # 重开钟楼
            return ["bell_tower", None, None, 0]
        elif start_mode == 3:  # 重开异时层
            return ["divergence", None, None, 0]
        elif start_mode == 4:  # 重开道中,33层bug很可能来自这里,考虑错误触发奖励识别
            return ["continuous", output_battle_list("continuous_powerful_enemy"), None, 0]
        elif start_mode == 5:  # 重开炽天使遭遇战
            return ["sss_1f", output_battle_list("seraph_skirmish_sim_1f"), None, 0]
        else:
            print("重开错误")
            return [None, None, None, 0]

    def enter_battle_in_special_mode(self, start_mode: int, count_number: list, if_complete: bool = False) -> bool:
        """特殊模式下重开战斗,count_number为重开把数和当前关卡层数的计数器"""
        self.log_print(get_time_str() + " (" + str(count_number[0] + 1) + ")")  # 打印战斗次数
        if (start_mode in [1, 2, 3]) and (count_number[0] == 0):
            self.update_battle_list_by_start_mode()
            # 只执行了一次,有可能是在暂停后继续运行,仅在此更新一次战斗列表,减少文件读取造成的长时间运行卡顿
        self.inherited_order_of_stations = None  # 重开自然从头开始
        self.inherited_turn = 0
        flag: bool = True
        if start_mode == 1:
            flag = self.enter_score_attack()
        elif start_mode == 2:
            flag = self.enter_bell_tower()
        elif start_mode == 3:
            if if_complete:  # 打完了,说明用了一次梦泪
                self.ability_up_limit = self.ability_up_limit - 1
            flag = self.enter_divergence(self.divergence_enemy_number, self.ability_up_number, self.ability_up_limit)
        elif start_mode == 4:  # 道中模式
            if if_complete:
                self.wait_next_battle(count_number)  # 自动识别是否精英选战斗方案
            else:  # 战斗失败,停止
                self.hbr_auto_battle_stop()
        elif start_mode == 5:  # 炽天使遭遇战预载
            if self.wait_card_choose():  # 等待选卡界面弹出
                next_list = seraph_skirmish_sim_recognize(count_number[1] + 1, count_number[2])
                if self.is_test:
                    print(count_number, next_list[3])
                if if_complete and next_list[2]:  # count_number[1]当前层数
                    count_number[1] = count_number[1] + 1  # 层数+1,第1层打完是1,第二层打完
                    count_number[2] = next_list[3]  # 更新词条剩余刷新次数
                    hbr_left_click(self.hbr_handle, next_list[2])  # 选词条
                    if count_number[1] == 4:  # 全过了就该停了,多打一把排名往后去了
                        return False
                    else:
                        self.battle_list_all_teams = next_list[0]
                        self.sp_check_list = next_list[1]
                else:  # 准备重开,点一下卡牌位置,退出重开
                    count_number[1] = 0  # 清空层数
                    count_number[2] = 5  # 清空词条刷新次数
                    press_key_list(["d", "enter"])  # 随便选一个词条进下一轮
                    self.exit_battle(self.if_skip_plot)  # 重开
                    self.enter_sss_battle()
                    self.update_battle_list_by_start_mode()
            else:  # 可能被打死或因sp不够回退到了初始界面
                self.enter_sss_battle()
                self.update_battle_list_by_start_mode()
        count_number[0] = count_number[0] + 1
        if flag:
            return True
        else:
            return False
    # 以上是新增模式必须维护的函数


if __name__ == '__main__':
    hbr = Application()
    hbr.hbr_auto_battle_run()
    # hbr.hbr_handle = hbr_get_handle()
    # hbr.wait_card_choose()
    # hbr.enter_sss_battle()
    # hbr.enter_bell_tower()
    # hbr.enter_divergence(4,2,1)
