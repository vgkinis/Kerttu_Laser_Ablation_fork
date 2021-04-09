from PyQt5.QtWidgets import (QWidget, QPushButton, QTextEdit, QGridLayout, QComboBox, QHBoxLayout, QVBoxLayout, QApplication, QLCDNumber,
                             QLabel, QMainWindow, qApp, QSpacerItem, QSizePolicy, QFrame, QCheckBox)
from PyQt5.QtCore import pyqtSlot, QRect, Qt, QThread, pyqtSignal
from PyQt5 import QtCore
from PyQt5.QtGui import QColor, QPalette, QPainter, QBrush, QPen
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

import sys
import time
import pytz
from datetime import datetime
from serial.tools import list_ports
import functools
import schedule
import csv
import os

from general_functions import *
from linear_stage import LinearStage
from laser import Laser


class WorkerThread(QThread):
    signals = pyqtSignal(dict, name='signals')
    def __init__(self, parent=None):
        QThread.__init__(self)

    def run(self):
        # Variables for discrete sampling and calibration
        self.discrete_sampling = False
        self.discrete_timer = None
        self.calibrating = False
        self.calibrate_start_count = None
        self.calibrated = False

        self.linear_stage_connected = False
        self.laser_connected = False

        # Create a linear stage instance
        self.ls = LinearStage(json_path="linear_stage.json")
        self.ls.read_json()

        # Create a laser instance
        self.laser = Laser()

        self.data_dict = {}
        self.data_dict.update(self.ls.data_dict)
        self.data_dict.update(self.laser.data_dict)

        while True:
            if self.laser_connected:
                self.laser.ping_laser_module()

            if self.linear_stage_connected:
                try:
                    # Get feedback
                    self.ls.ping_arduino()
                    motor_data = self.ls.serial_read()
                    self.data_dict.update(motor_data)

                    # Calibrate or perform discrete movement if it has been chosen.
                    self.calibrate_sys()
                    self.discrete_movement()

                except Exception as e:
                    print(e)
                    continue

            if self.laser_connected:
                try:
                    laser_data = self.laser.serial_read()
                    self.data_dict.update(laser_data)
                except:
                    continue

            if self.laser_connected or self.linear_stage_connected:
                self.signals.emit(self.data_dict)
                schedule.run_pending()


    def start_data_logger(self):
        # Data files
        dir_data = os.path.join(os.getcwd(),"Data")
        time_stamp = datetime.now(pytz.timezone("Europe/Copenhagen")).strftime("%Y-%m-%d %H.%M.%S.%f+%z")
        self.data_filename = os.path.join(dir_data,"LA_data_" + str(time_stamp) + ".csv")
        with open(self.data_filename,"a") as f:
            column_names = list(self.ls.data_dict)
            column_names += ["rep_rate_kHz", "energy_nJ", "energy_uJ", "epoch_time"]
            writer = csv.writer(f, delimiter=",")
            # Pad the header elements
            maxlen = len(max(column_names, key=len))
            writer.writerow([(' ' * (maxlen - len(x))) + x for x in column_names])

        schedule.every(1).seconds.do(self.data_logger)

    def connect_laser(self):
        ports = (list(list_ports.comports()))
        print("Establishing a connection with the laser ...")
        for port in ports:
            #print(port.manufacturer, port.device, port.description)
            if "FTDI" in port.manufacturer:
                try:
                    self.laser.start_serial(port.device)
                    time.sleep(2)
                    self.laser_connected = True
                    self.start_data_logger()
                except Exception as e:
                    print("Exception in connect_laser():", e)
        if self.laser_connected == False:
            print("Cannot find the laser")

    def connect_linear_stage(self):
        ports = (list(list_ports.comports()))
        print("Establishing a connection with the linear stage ...")
        for port in ports:
            if "Arduino" in port.manufacturer:
                try:
                    self.ls.start_serial(port.device)
                    time.sleep(2)
                    self.linear_stage_connected = True
                    self.start_data_logger()
                except Exception as e:
                    print(e)
        if self.linear_stage_connected == False:
            print("Cannot find the linear stage")

    def data_logger(self):
        with open(self.data_filename,"a") as f:
            writer = csv.writer(f, delimiter=",")
            data = self.data_dict
            data_formatted = {"loop_time": "{:13.3f}".format(data["loop_time"]),
                            "loop_time_min": "{:13.3f}".format(data["loop_time_min"]),
                            "pos_steps": "{:13}".format(data["pos_steps"]),
                            "pos_rev": "{:13.3f}".format(data["pos_rev"]),
                            "pos_mm": "{:13.3f}".format(data["pos_mm"]),
                            "dis_steps": "{:13}".format(data["dis_steps"]),
                            "dis_mm": "{:13.3f}".format(data["dis_mm"]),
                            "dis_rev": "{:13.3f}".format(data["dis_rev"]),
                            "spd_us/step": "{:13.3f}".format(data["spd_us/step"]),
                            "spd_step/s": "{:13.3f}".format(data["spd_step/s"]),
                            "spd_rev/s": "{:13.3f}".format(data["spd_rev/s"]),
                            "spd_mm/s": "{:13.3f}".format(data["spd_mm/s"]),
                            "direction": "{:13}".format(data["direction"]),
                            "event_code": "{:13}".format(data["event_code"]),
                            "rep_rate_kHz": "{:13.3f}".format(data["rep_rate_kHz"]),
                            "energy_nJ": "{:13.3f}".format(data["energy_nJ"]),
                            "energy_uJ": "{:13.3f}".format(data["energy_uJ"]),
                            "epoch_time": "{:13.3f}".format(data["epoch_time"])
                            }
            writer.writerow(data_formatted.values())

    def calibrate_sys(self):
        if self.calibrating == True:
            if self.ls.event_code == 0:
                self.ls.set_event_code(4)
                self.ls.set_dir(-1)
                self.ls.move_dis(self.ls.stage_length, "mm")
            elif self.ls.event_code == 2:
                self.ls.set_event_code(4)
                self.ls.set_dir(1)
                self.calibrate_start_count = self.ls.abs_pos_stp
                self.ls.move_dis(self.ls.stage_length, "mm")
            elif self.ls.event_code == 1 and self.calibrate_start_count != None:
                full_ls_range = abs(self.ls.abs_pos_stp - self.calibrate_start_count)
                half_ls_range = abs(full_ls_range)/2
                print("The full range of the linear stage is measured to be: {0} steps, {1} mm.".format(full_ls_range, self.ls.stp_to_mm(full_ls_range)))
                print("The half range of the linear stage is measured to be: {0} steps, {1} mm.".format(half_ls_range, self.ls.stp_to_mm(half_ls_range)))
                self.ls.set_dir(-1)
                self.calibrate_start_count = None
                new_abs_pos = half_ls_range
                self.ls.set_abs_pos_stp(new_abs_pos)
                self.ls.set_event_code(0)
                dis = abs(new_abs_pos - 0)
                time.sleep(1)
                self.ls.move_dis(dis, "steps")
                self.calibrating = False
                self.calibrated = True

    def discrete_startup(self, dis_interval, dis_interval_unit, time_interval, nr, with_laser):
        self.discrete_sampling = True
        self.discrete_dis = dis_interval
        self.discrete_dis_unit = dis_interval_unit
        self.discrete_time = time_interval
        self.discrete_laser = with_laser
        if self.discrete_laser == True:
            self.laser.go_to_standby()
        self.ls.set_event_code(4)
        self.ls.move_dis(self.discrete_dis, self.discrete_dis_unit)
        self.discrete_nr = nr-1

    def discrete_movement(self):
        if self.discrete_sampling == True:
            # Check if motor is moving
            if self.ls.dis_stp == 0:
                # Check if there are repetitons to do
                if self.discrete_nr > 0:
                    # Start the timer
                    if self.discrete_timer == None:
                        if self.discrete_laser == True:
                            self.laser.enable_laser()
                        self.discrete_timer = time.time()
                    # Move the next distance interval if waiting time is over
                    if self.discrete_timer + self.discrete_time <= time.time():
                        if self.discrete_laser == True:
                            self.laser.go_to_standby()
                        #print(time.time() - self.discrete_timer)
                        self.discrete_move_one_interval()
                # Reset the event code and finish discrete sampling.
                else:
                    self.ls.set_event_code(0)
                    self.discrete_sampling = False


    def discrete_move_one_interval(self):
        self.ls.move_dis(self.discrete_dis, self.discrete_dis_unit)
        self.discrete_nr -= 1
        self.discrete_timer = None

class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title='Laser Ablation'
        self.left=10
        self.top=10
        self.width=1290
        self.height=720
        self.setMinimumSize(1290, 720)
        self.initUI()

    def initUI(self):

        self.calibrating = False
        self.calibrated = False
        self.discrete_sampling = False

        central = QWidget(self)

        mainLayout = QGridLayout(central)

        self.setWindowTitle(self.title)
        self.setGeometry(self.left,self.top,self.width,self.height)

        horizontalSpacer1 = QSpacerItem(88, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        horizontalSpacer2 = QSpacerItem(30, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        verticalSpacer1 = QSpacerItem(0, 120, QSizePolicy.Minimum, QSizePolicy.Expanding)
        verticalSpacer2 = QSpacerItem(0, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)


# ---------------------------------- Position ----------------------------------
        motorLabelLayout = QHBoxLayout()
        mainLayout.addLayout(motorLabelLayout, 0, 0)
        motorLabelLayout.setAlignment(Qt.AlignCenter)

        self.labelMotor = QLabel('Linear Stage Control', self)
        self.labelMotor.setStyleSheet("QLabel {font: Times New Roman; font-size: 18px}")
        motorLabelLayout.addWidget(self.labelMotor)

        posLabelLayout = QHBoxLayout()
        mainLayout.addLayout(posLabelLayout, 1, 0)
        posLabelLayout.setAlignment(Qt.AlignLeft)
        posLabelLayout.addItem(horizontalSpacer2)

        self.labelPos = QLabel('Absolute Position', self)
        self.labelPos.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px}")
        posLabelLayout.addWidget(self.labelPos)

        posLayout = QHBoxLayout()
        mainLayout.addLayout(posLayout, 2, 0)
        posLayout.addItem(horizontalSpacer2)

        self.textEditPos = QTextEdit(self)
        self.textEditPos.setFixedSize(88, 34)
        posLayout.addWidget(self.textEditPos)
        posLayout.addItem(horizontalSpacer2)

        self.comboBoxPos = QComboBox(self)
        self.comboBoxPos.addItems(["mm", "steps", "rev"])
        self.comboBoxPos.setFixedSize(88, 34)
        posLayout.addWidget(self.comboBoxPos)
        posLayout.addItem(horizontalSpacer2)

        self.pushButtonPos = QPushButton('Move', self)
        self.pushButtonPos.setFixedSize(88, 34)
        posLayout.addWidget(self.pushButtonPos)
        posLayout.addItem(horizontalSpacer2)

        self.ledPos = QLabel(self)
        self.ledPos.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        posLayout.addWidget(self.ledPos)
        posLayout.addItem(horizontalSpacer2)

        self.lcdNumberPos = QLCDNumber(self)
        self.lcdNumberPos.setFixedSize(100, 34)
        set_lcd_style(self.lcdNumberPos)
        posLayout.addWidget(self.lcdNumberPos)
        posLayout.addItem(horizontalSpacer2)

        self.comboBoxPosFb = QComboBox(self)
        self.comboBoxPosFb.addItems(["mm", "steps", "rev"])
        self.comboBoxPosFb.setFixedSize(88, 34)
        posLayout.addWidget(self.comboBoxPosFb)
        posLayout.addItem(horizontalSpacer2)

# ---------------------------------- Distance ----------------------------------

        disLabelLayout = QHBoxLayout()
        mainLayout.addLayout(disLabelLayout, 3, 0)
        disLabelLayout.setAlignment(Qt.AlignLeft)
        disLabelLayout.addItem(horizontalSpacer2)

        self.labelDis = QLabel('Distance', self)
        self.labelDis.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px}")
        self.labelDis.setFixedSize(88, 34)
        disLabelLayout.addWidget(self.labelDis)

        disLayout = QHBoxLayout()
        mainLayout.addLayout(disLayout, 4, 0)
        disLayout.addItem(horizontalSpacer2)

        self.textEditDis = QTextEdit(self)
        self.textEditDis.setFixedSize(88, 34)
        disLayout.addWidget(self.textEditDis)
        disLayout.addItem(horizontalSpacer2)

        self.comboBoxDis = QComboBox(self)
        self.comboBoxDis.addItems(["mm", "steps", "rev"])
        self.comboBoxDis.setFixedSize(88, 34)
        disLayout.addWidget(self.comboBoxDis)
        disLayout.addItem(horizontalSpacer2)

        self.pushButtonDis = QPushButton('Move', self)
        self.pushButtonDis.setFixedSize(88, 34)
        disLayout.addWidget(self.pushButtonDis)
        disLayout.addItem(horizontalSpacer2)

        self.ledDis = QLabel(self)
        self.ledDis.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        disLayout.addWidget(self.ledDis)
        disLayout.addItem(horizontalSpacer2)

        self.lcdNumberDis = QLCDNumber(self)
        self.lcdNumberDis.setFixedSize(100, 34)
        set_lcd_style(self.lcdNumberDis)
        disLayout.addWidget(self.lcdNumberDis)
        disLayout.addItem(horizontalSpacer2)

        self.comboBoxDisFb = QComboBox(self)
        self.comboBoxDisFb.addItems(["mm", "steps", "rev"])
        self.comboBoxDisFb.setFixedSize(88, 34)
        disLayout.addWidget(self.comboBoxDisFb)
        disLayout.addItem(horizontalSpacer2)

# ----------------------------------- Speed ------------------------------------

        spdLabelLayout = QHBoxLayout()
        mainLayout.addLayout(spdLabelLayout, 5, 0)
        spdLabelLayout.setAlignment(Qt.AlignLeft)
        spdLabelLayout.addItem(horizontalSpacer2)

        self.labelSpd = QLabel('Speed', self)
        self.labelSpd.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px}")
        self.labelSpd.setFixedSize(88, 34)
        spdLabelLayout.addWidget(self.labelSpd)

        spdLayout = QHBoxLayout()
        mainLayout.addLayout(spdLayout, 6, 0)
        spdLayout.addItem(horizontalSpacer2)

        self.textEditSpd = QTextEdit(self)
        self.textEditSpd.setFixedSize(88, 34)
        spdLayout.addWidget(self.textEditSpd)
        spdLayout.addItem(horizontalSpacer2)

        self.comboBoxSpd = QComboBox(self)
        self.comboBoxSpd.addItems(["mm/s", "step/s", "rev/s", "us/step"])
        self.comboBoxSpd.setFixedSize(88, 34)
        spdLayout.addWidget(self.comboBoxSpd)
        spdLayout.addItem(horizontalSpacer2)

        self.pushButtonSpd = QPushButton('Set', self)
        self.pushButtonSpd.setFixedSize(88, 34)
        spdLayout.addWidget(self.pushButtonSpd)
        spdLayout.addItem(horizontalSpacer2)

        self.ledSpd = QLabel(self)
        self.ledSpd.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        spdLayout.addWidget(self.ledSpd)
        spdLayout.addItem(horizontalSpacer2)

        self.lcdNumberSpd = QLCDNumber(self)
        self.lcdNumberSpd.setFixedSize(100, 34)
        set_lcd_style(self.lcdNumberSpd)
        spdLayout.addWidget(self.lcdNumberSpd)
        spdLayout.addItem(horizontalSpacer2)

        self.comboBoxSpdFb = QComboBox(self)
        self.comboBoxSpdFb.addItems(["mm/s", "step/s", "rev/s", "us/step"])
        self.comboBoxSpdFb.setFixedSize(88, 34)
        spdLayout.addWidget(self.comboBoxSpdFb)
        spdLayout.addItem(horizontalSpacer2)

# --------------------------------- Direction ----------------------------------

        dirLabelLayout = QHBoxLayout()
        mainLayout.addLayout(dirLabelLayout, 7, 0)
        dirLabelLayout.setAlignment(Qt.AlignLeft)
        dirLabelLayout.addItem(horizontalSpacer2)

        self.labelDir = QLabel('Direction', self)
        self.labelDir.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px}")
        self.labelDir.setFixedSize(111, 34)
        dirLabelLayout.addWidget(self.labelDir)

        dirLayout = QHBoxLayout()
        mainLayout.addLayout(dirLayout, 8, 0)
        dirLayout.addItem(horizontalSpacer2)

        self.textEditDir = QTextEdit(self)
        self.textEditDir.setFixedSize(88, 34)
        dirLayout.addWidget(self.textEditDir)
        dirLayout.addItem(horizontalSpacer2)
        dirLayout.addItem(horizontalSpacer1)
        dirLayout.addItem(horizontalSpacer2)

        self.pushButtonDir = QPushButton('Set', self)
        self.pushButtonDir.setFixedSize(88, 34)
        dirLayout.addWidget(self.pushButtonDir)
        dirLayout.addItem(horizontalSpacer2)

        self.ledDir = QLabel(self)
        self.ledDir.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        dirLayout.addWidget(self.ledDir)
        dirLayout.addItem(horizontalSpacer2)

        self.lcdNumberDir = QLCDNumber(self)
        self.lcdNumberDir.setFixedSize(100, 34)
        set_lcd_style(self.lcdNumberDir)
        dirLayout.addWidget(self.lcdNumberDir)
        dirLayout.addItem(horizontalSpacer2)
        dirLayout.addItem(horizontalSpacer1)
        dirLayout.addItem(horizontalSpacer2)

        emptyLayout1 = QHBoxLayout()
        mainLayout.addLayout(emptyLayout1, 9, 0)
        emptyLayout1.setAlignment(Qt.AlignLeft)
        emptyLayout1.addItem(horizontalSpacer2)

        self.emptyLabel1 = QLabel(' ', self)
        self.emptyLabel1.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px}")
        self.emptyLabel1.setFixedSize(111, 34)
        emptyLayout1.addWidget(self.emptyLabel1)


# --------------------------------- Varia --------------------------------------
        variaLayout = QHBoxLayout()

        mainLayout.addLayout(variaLayout, 10, 0)
        variaLayout.setAlignment(Qt.AlignLeft)
        variaLayout.addItem(horizontalSpacer2)

        self.pushButtonC = QPushButton('Calibrate', self)
        self.pushButtonC.setFixedSize(88, 34)
        variaLayout.addWidget(self.pushButtonC)
        variaLayout.addItem(horizontalSpacer2)

        self.pushButtonR = QPushButton('Reset', self)
        self.pushButtonR.setFixedSize(88, 34)
        variaLayout.addWidget(self.pushButtonR)
        variaLayout.addItem(QSpacerItem(128, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.labelEvent = QLabel('Event Code', self)
        variaLayout.addWidget(self.labelEvent)
        variaLayout.addItem(QSpacerItem(10, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.lcdNumberEvent = QLCDNumber(self)
        self.lcdNumberEvent.setFixedSize(100, 0)
        set_lcd_style(self.lcdNumberEvent)
        variaLayout.addWidget(self.lcdNumberEvent)


# --------------------------------- Graph --------------------------------------

        graphLayout = QHBoxLayout()
        mainLayout.addLayout(graphLayout, 11, 0)

        self.figure_ls = plt.figure()
        self.figure_ls.set_figheight(0.5)
        self.figure_ls.set_figwidth(5)
        self.canvas_ls = FigureCanvas(self.figure_ls)

        graphLayout.addWidget(self.canvas_ls)

        variaLayout.addItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))


# --------------------------- Discrete movement --------------------------------

        discreteLabelLayout = QHBoxLayout()
        mainLayout.addLayout(discreteLabelLayout, 12, 0)
        discreteLabelLayout.setAlignment(Qt.AlignCenter)
        discreteLabelLayout.addItem(horizontalSpacer2)

        self.labelDiscrete = QLabel('Discrete Movement', self)
        self.labelDiscrete.setFixedSize(200, 34)
        self.labelDiscrete.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px}")
        discreteLabelLayout.addWidget(self.labelDiscrete)
        discreteLabelLayout.addItem(QSpacerItem(0, 50, QSizePolicy.Minimum, QSizePolicy.Expanding))

        discreteTxtLayout = QHBoxLayout()

        self.labelDiscrete1 = QLabel('Distance Interval', self)
        self.labelDiscrete1.setFixedSize(100, 34)
        self.labelDiscrete1.setStyleSheet("QLabel {font-size: 12px; color: #263470}")

        self.labelDiscrete2 = QLabel('Time Interval', self)
        self.labelDiscrete2.setFixedSize(80, 34)
        self.labelDiscrete2.setStyleSheet("QLabel {font-size: 12px; color: #263470}")

        self.labelDiscrete3 = QLabel('Nr of Repetitions', self)
        self.labelDiscrete3.setFixedSize(100, 34)
        self.labelDiscrete3.setStyleSheet("QLabel {font-size: 12px; color: #263470}")

        discreteLayout1 = QHBoxLayout()
        mainLayout.addLayout(discreteLayout1, 13, 0)
        discreteLayout1.setAlignment(Qt.AlignCenter)

        discreteLayout1.addWidget(self.labelDiscrete1)

        self.textEditDiscreteDis = QTextEdit(self)
        self.textEditDiscreteDis.setFixedSize(80, 34)
        discreteLayout1.addWidget(self.textEditDiscreteDis)

        self.comboBoxDiscrete = QComboBox(self)
        self.comboBoxDiscrete.addItems(["mm", "steps", "rev"])
        self.comboBoxDiscrete.setFixedSize(65, 34)
        discreteLayout1.addWidget(self.comboBoxDiscrete)

        add_custom_spacer(20,34,discreteLayout1)
        discreteLayout1.addWidget(self.labelDiscrete2)

        self.textEditDiscreteTime = QTextEdit(self)
        self.textEditDiscreteTime.setFixedSize(80, 34)
        discreteLayout1.addWidget(self.textEditDiscreteTime)

        self.labelDiscrete5 = QLabel('s', self)
        self.labelDiscrete5.setFixedSize(10, 34)
        discreteLayout1.addWidget(self.labelDiscrete5)

        add_custom_spacer(20,34,discreteLayout1)
        discreteLayout1.addWidget(self.labelDiscrete3)

        self.textEditDiscreteNr = QTextEdit(self)
        self.textEditDiscreteNr.setFixedSize(80, 34)
        discreteLayout1.addWidget(self.textEditDiscreteNr)

        discreteLayout2 = QHBoxLayout()
        mainLayout.addLayout(discreteLayout2, 14, 0)
        discreteLayout2.setAlignment(Qt.AlignCenter)

        self.checkBoxDiscreteLaser = QCheckBox("Enable laser emission during discrete movement",self)
        self.checkBoxDiscreteLaser.resize(320,40)
        discreteLayout2.addWidget(self.checkBoxDiscreteLaser)
        discreteLayout2.addItem(horizontalSpacer2)

        self.pushButtonDiscrete = QPushButton('Start', self)
        self.pushButtonDiscrete.setFixedSize(88, 34)
        discreteLayout2.addWidget(self.pushButtonDiscrete)

        self.ledDiscrete = QLabel(self)
        self.ledDiscrete.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        discreteLayout2.addWidget(self.ledDiscrete)
        discreteLayout2.addItem(horizontalSpacer2)
        discreteLayout2.addItem(QSpacerItem(0, 80, QSizePolicy.Minimum, QSizePolicy.Expanding))

# ------------------------------- Laser ----------------------------------------

        laserLabelLayout = QHBoxLayout()
        mainLayout.addLayout(laserLabelLayout, 0, 1)
        laserLabelLayout.setAlignment(Qt.AlignCenter)
        laserLabelLayout.addItem(horizontalSpacer2)

        self.labelLaser = QLabel('Laser Control', self)
        self.labelLaser.setStyleSheet("QLabel {font: Times New Roman; font-size: 18px}")
        laserLabelLayout.addWidget(self.labelLaser)

        """
        self.ledLaserEnable = QLabel(self)
        self.ledLaserEnable.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        laserLayoutEnable.addWidget(self.ledLaserEnable)"""


        laserLayoutLabelRep = QHBoxLayout()
        mainLayout.addLayout(laserLayoutLabelRep, 1, 1)
        laserLayoutLabelRep.setAlignment(Qt.AlignLeft)
        laserLayoutLabelRep.addItem(horizontalSpacer2)

        self.labelLaserRep= QLabel('Repetition rate', self)
        self.labelLaserRep.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px}")
        self.labelLaserRep.setFixedSize(100, 34)
        laserLayoutLabelRep.addWidget(self.labelLaserRep)

        laserLayoutRep = QHBoxLayout()
        mainLayout.addLayout(laserLayoutRep, 2, 1)
        laserLayoutRep.setAlignment(Qt.AlignLeft)
        laserLayoutRep.addItem(horizontalSpacer2)

        self.comboBoxLaserRep = QComboBox(self)
        rep_rates_kHz = {0:"  50.000 kHz", 1:" 100.000 kHz", 2:" 200.000 kHz", 3:" 299.625 kHz", 4:" 400.000 kHz", 5:" 500.000 kHz",
                                6:" 597.015 kHz", 7:" 707.965 kHz", 8:" 800.000 kHz", 9:" 898.876 kHz", 10:"1 000.000 kHz"}
        self.comboBoxLaserRep.addItems(rep_rates_kHz.values())
        self.comboBoxLaserRep.setFixedSize(120, 34)
        laserLayoutRep.addWidget(self.comboBoxLaserRep)
        laserLayoutRep.addItem(QSpacerItem(68, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.pushButtonLaserRepSet = QPushButton('Set', self)
        self.pushButtonLaserRepSet.setFixedSize(88, 34)
        laserLayoutRep.addWidget(self.pushButtonLaserRepSet)
        laserLayoutRep.addItem(horizontalSpacer2)

        self.lcdNumberLaserRep = QLCDNumber(self)
        self.lcdNumberLaserRep.setFixedSize(100, 34)
        set_lcd_style(self.lcdNumberLaserRep)
        laserLayoutRep.addWidget(self.lcdNumberLaserRep)

        self.labelLaserRep2 = QLabel('kHz', self)
        self.labelLaserRep2.setFixedSize(25, 34)
        laserLayoutRep.addWidget(self.labelLaserRep2)
        laserLayoutRep.addItem(horizontalSpacer2)

        laserLayoutLabelEnergy = QHBoxLayout()
        mainLayout.addLayout(laserLayoutLabelEnergy, 3, 1)
        laserLayoutLabelEnergy.setAlignment(Qt.AlignLeft)
        laserLayoutLabelEnergy.addItem(horizontalSpacer2)

        self.labelLaserLabelEnergy= QLabel('Pulse energy', self)
        self.labelLaserLabelEnergy.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px}")
        self.labelLaserLabelEnergy.setFixedSize(100, 34)
        laserLayoutLabelEnergy.addWidget(self.labelLaserLabelEnergy)

        laserLayoutEnergy = QHBoxLayout()
        mainLayout.addLayout(laserLayoutEnergy, 4, 1)
        laserLayoutEnergy.setAlignment(Qt.AlignLeft)
        laserLayoutEnergy.addItem(horizontalSpacer2)

        self.textEditEnergy = QTextEdit(self)
        self.textEditEnergy.setFixedSize(88, 34)
        laserLayoutEnergy.addWidget(self.textEditEnergy)
        #laserLayoutEnergy.addItem(horizontalSpacer2)

        self.comboBoxLaserEnergy = QComboBox(self)
        self.comboBoxLaserEnergy.addItems(["uJ", "nJ"])
        self.comboBoxLaserEnergy.setFixedSize(65, 34)
        laserLayoutEnergy.addWidget(self.comboBoxLaserEnergy)
        laserLayoutEnergy.addItem(horizontalSpacer2)

        self.pushButtonLaserEnergySet = QPushButton('Set', self)
        self.pushButtonLaserEnergySet.setFixedSize(88, 34)
        laserLayoutEnergy.addWidget(self.pushButtonLaserEnergySet)
        laserLayoutEnergy.addItem(horizontalSpacer2)

        self.lcdNumberLaserEnergy = QLCDNumber(self)
        self.lcdNumberLaserEnergy.setFixedSize(100, 34)
        set_lcd_style(self.lcdNumberLaserEnergy)
        laserLayoutEnergy.addWidget(self.lcdNumberLaserEnergy)

        self.comboBoxLaserEnergy2 = QComboBox(self)
        self.comboBoxLaserEnergy2.addItems(["uJ", "nJ"])
        self.comboBoxLaserEnergy2.setFixedSize(65, 34)
        laserLayoutEnergy.addWidget(self.comboBoxLaserEnergy2)

        laserLayoutModes = QHBoxLayout()
        mainLayout.addLayout(laserLayoutModes, 6, 1)
        laserLayoutModes.setAlignment(Qt.AlignCenter)
        laserLayoutModes.addItem(QSpacerItem(50, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.pushButtonLaserListen = QPushButton('Listen', self)
        self.pushButtonLaserListen.setFixedSize(88, 34)
        self.pushButtonLaserListen.setStyleSheet("background-color: #dbdbdb")
        laserLayoutModes.addWidget(self.pushButtonLaserListen)
        laserLayoutModes.addItem(horizontalSpacer2)

        self.pushButtonLaserStandby = QPushButton('Standby', self)
        self.pushButtonLaserStandby.setFixedSize(88, 34)
        self.pushButtonLaserStandby.setStyleSheet("background-color: #dbdbdb")
        laserLayoutModes.addWidget(self.pushButtonLaserStandby)
        laserLayoutModes.addItem(horizontalSpacer2)

        self.pushButtonLaserEnable = QPushButton('Enable', self)
        self.pushButtonLaserEnable.setFixedSize(88, 34)
        self.pushButtonLaserEnable.setStyleSheet("background-color: #dbdbdb")
        laserLayoutModes.addWidget(self.pushButtonLaserEnable)
        laserLayoutModes.addItem(horizontalSpacer2)

        laserLayoutStatus1 = QHBoxLayout()
        mainLayout.addLayout(laserLayoutStatus1, 8, 1)
        laserLayoutStatus1.setAlignment(Qt.AlignLeft)
        laserLayoutStatus1.addItem(horizontalSpacer2)

        self.labelStatusLaserOn= QLabel('Laser on enabled', self)
        self.labelStatusLaserOn.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px; color: #263470}")
        self.labelStatusLaserOn.setFixedSize(170, 34)
        laserLayoutStatus1.addWidget(self.labelStatusLaserOn)

        self.ledLaserOn = QLabel(self)
        self.ledLaserOn.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        laserLayoutStatus1.addWidget(self.ledLaserOn)
        laserLayoutStatus1.addItem(QSpacerItem(80, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.labelStatusListen= QLabel('Listen', self)
        self.labelStatusListen.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px; color: #263470}")
        self.labelStatusListen.setFixedSize(170, 34)
        laserLayoutStatus1.addWidget(self.labelStatusListen)

        self.ledLaserListen = QLabel(self)
        self.ledLaserListen.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        laserLayoutStatus1.addWidget(self.ledLaserListen)

        laserLayoutStatus2 = QHBoxLayout()
        mainLayout.addLayout(laserLayoutStatus2, 9, 1)
        laserLayoutStatus2.setAlignment(Qt.AlignLeft)
        laserLayoutStatus2.addItem(horizontalSpacer2)

        self.labelStatusLaserOnDis= QLabel('Laser on disabled', self)
        self.labelStatusLaserOnDis.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px; color: #263470}")
        self.labelStatusLaserOnDis.setFixedSize(170, 34)
        laserLayoutStatus2.addWidget(self.labelStatusLaserOnDis)

        self.ledLaserOnDis = QLabel(self)
        self.ledLaserOnDis.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        laserLayoutStatus2.addWidget(self.ledLaserOnDis)
        laserLayoutStatus2.addItem(QSpacerItem(80, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.labelStatusWarning= QLabel('Warning', self)
        self.labelStatusWarning.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px; color: #263470}")
        self.labelStatusWarning.setFixedSize(170, 34)
        laserLayoutStatus2.addWidget(self.labelStatusWarning)

        self.ledLaserWarning = QLabel(self)
        self.ledLaserWarning.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        laserLayoutStatus2.addWidget(self.ledLaserWarning)

        laserLayoutStatus3 = QHBoxLayout()
        mainLayout.addLayout(laserLayoutStatus3, 10, 1)
        laserLayoutStatus3.setAlignment(Qt.AlignLeft)
        laserLayoutStatus3.addItem(horizontalSpacer2)

        self.labelStatusStandby= QLabel('Standby', self)
        self.labelStatusStandby.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px; color: #263470}")
        self.labelStatusStandby.setFixedSize(170, 34)
        laserLayoutStatus3.addWidget(self.labelStatusStandby)

        self.ledLaserStandby = QLabel(self)
        self.ledLaserStandby.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        laserLayoutStatus3.addWidget(self.ledLaserStandby)
        laserLayoutStatus3.addItem(QSpacerItem(80, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.labelStatusError= QLabel('Error', self)
        self.labelStatusError.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px; color: #263470}")
        self.labelStatusError.setFixedSize(170, 34)
        laserLayoutStatus3.addWidget(self.labelStatusError)

        self.ledLaserError = QLabel(self)
        self.ledLaserError.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        laserLayoutStatus3.addWidget(self.ledLaserError)

        laserLayoutStatus4 = QHBoxLayout()
        mainLayout.addLayout(laserLayoutStatus4, 11, 1)
        laserLayoutStatus4.setAlignment(Qt.AlignLeft)
        laserLayoutStatus4.addItem(horizontalSpacer2)

        self.labelStatusSetup= QLabel('Setup', self)
        self.labelStatusSetup.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px; color: #263470}")
        self.labelStatusSetup.setFixedSize(170, 34)
        laserLayoutStatus4.addWidget(self.labelStatusSetup)

        self.ledLaserSetup = QLabel(self)
        self.ledLaserSetup.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        laserLayoutStatus4.addWidget(self.ledLaserSetup)
        laserLayoutStatus4.addItem(QSpacerItem(80, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.labelStatusPower= QLabel('Power', self)
        self.labelStatusPower.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px; color: #263470}")
        self.labelStatusPower.setFixedSize(170, 34)
        laserLayoutStatus4.addWidget(self.labelStatusPower)

        self.ledLaserPower = QLabel(self)
        self.ledLaserPower.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        laserLayoutStatus4.addWidget(self.ledLaserPower)

# ---------------------------- Connect -----------------------------------------

        connectLabelLayout = QHBoxLayout()
        mainLayout.addLayout(connectLabelLayout, 12, 1)
        connectLabelLayout.setAlignment(Qt.AlignCenter)
        connectLabelLayout.addItem(horizontalSpacer2)

        self.labelConnect = QLabel('Connect', self)
        self.labelConnect.setStyleSheet("QLabel {font: Times New Roman; font-size: 18px}")
        connectLabelLayout.addWidget(self.labelConnect)

        connectLayoutLS = QHBoxLayout()
        mainLayout.addLayout(connectLayoutLS, 13, 1)
        connectLayoutLS.setAlignment(Qt.AlignLeft)
        connectLayoutLS.addItem(horizontalSpacer2)

        self.labelConnectLS = QLabel('Linear Stage', self)
        self.labelConnectLS.setFixedSize(100, 34)
        self.labelConnectLS.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px}")
        connectLayoutLS.addWidget(self.labelConnectLS)

        self.pushButtonConnectLS = QPushButton('Connect', self)
        self.pushButtonConnectLS.setFixedSize(88, 34)
        connectLayoutLS.addWidget(self.pushButtonConnectLS)
        connectLayoutLS.addItem(horizontalSpacer2)

        self.ledConnectLinearStage = QLabel(self)
        self.ledConnectLinearStage.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        connectLayoutLS.addWidget(self.ledConnectLinearStage)
        #connectLayoutLS.addItem(horizontalSpacer2)


        connectLayoutL = QHBoxLayout()
        mainLayout.addLayout(connectLayoutL, 14, 1)
        connectLayoutL.setAlignment(Qt.AlignLeft)
        connectLayoutL.addItem(horizontalSpacer2)

        self.labelConnectL = QLabel('Laser', self)
        self.labelConnectL.setFixedSize(100, 34)
        self.labelConnectL.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px}")
        connectLayoutL.addWidget(self.labelConnectL)

        self.pushButtonConnectL = QPushButton('Connect', self)
        self.pushButtonConnectL.setFixedSize(88, 34)
        connectLayoutL.addWidget(self.pushButtonConnectL)
        connectLayoutL.addItem(horizontalSpacer2)

        self.ledConnectLaser = QLabel(self)
        self.ledConnectLaser.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        connectLayoutL.addWidget(self.ledConnectLaser)
        connectLayoutL.addItem(horizontalSpacer2)



# -----------------------------------------------------------------------------
        self.wt=WorkerThread() # This is the thread object
        self.wt.start()
        self.wt.signals.connect(self.slot_method)
        self.pushButtonPos.clicked.connect(functools.partial(self.move_pos))
        self.pushButtonSpd.clicked.connect(functools.partial(self.set_spd))
        self.pushButtonDir.clicked.connect(functools.partial(self.set_dir))
        self.pushButtonDis.clicked.connect(functools.partial(self.move_dis))
        self.pushButtonR.clicked.connect(functools.partial(self.reset_sys))
        self.pushButtonC.clicked.connect(functools.partial(self.calibrate_sys))
        self.pushButtonDiscrete.clicked.connect(functools.partial(self.discrete_meas))

        self.pushButtonConnectLS.clicked.connect(functools.partial(self.wt.connect_linear_stage))
        self.pushButtonConnectL.clicked.connect(functools.partial(self.wt.connect_laser))

        self.pushButtonLaserEnergySet.clicked.connect(functools.partial(self.set_laser_energy))
        self.pushButtonLaserRepSet.clicked.connect(functools.partial(self.set_laser_rep_rate))
        self.pushButtonLaserListen.clicked.connect(functools.partial(self.wt.laser.go_to_listen))
        self.pushButtonLaserStandby.clicked.connect(functools.partial(self.wt.laser.go_to_standby))
        self.pushButtonLaserEnable.clicked.connect(functools.partial(self.wt.laser.enable_laser))

        app.aboutToQuit.connect(QApplication.instance().quit) #to stop the thread when closing the GUI


    def slot_method(self, data_dict):
        # Linear Stage parameters
        if self.wt.linear_stage_connected == True:
            self.lcdNumberPos.display(data_dict["pos_" + self.comboBoxPosFb.currentText()])
            self.lcdNumberDis.display(data_dict["dis_" + self.comboBoxDisFb.currentText()])
            self.lcdNumberSpd.display(data_dict["spd_" + self.comboBoxSpdFb.currentText()])
            self.lcdNumberDir.display(data_dict["direction"])
            self.lcdNumberEvent.display(data_dict["event_code"])

            abs_pos_mm = data_dict["pos_mm"]
            self.update_graph(abs_pos_mm)

            self.ledConnectLinearStage.setStyleSheet("QLabel {background-color : forestgreen; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")

        # Laser parameters
        if self.wt.laser_connected == True:
            self.lcdNumberLaserRep.display(data_dict["rep_rate_kHz"])
            self.lcdNumberLaserEnergy.display(data_dict["energy_" + self.comboBoxLaserEnergy2.currentText()])

            turn_led_on_off(self.ledLaserOn, data_dict["status_laser_on_enabled"])
            turn_led_on_off(self.ledLaserOnDis, data_dict["status_laser_on_disabled"])
            turn_led_on_off(self.ledLaserStandby, data_dict["status_standby"])
            turn_led_on_off(self.ledLaserSetup, data_dict["status_setup"])
            turn_led_on_off(self.ledLaserListen, data_dict["status_listen"])
            turn_led_on_off(self.ledLaserWarning, data_dict["status_warning"])
            turn_led_on_off(self.ledLaserError, data_dict["status_error"])
            turn_led_on_off(self.ledLaserPower, data_dict["status_power"])

            self.ledConnectLaser.setStyleSheet("QLabel {background-color : forestgreen; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")


    def move_pos(self):
        val = float(self.textEditPos.toPlainText())
        if self.wt.calibrating == False and self.wt.discrete_sampling == False:
            self.wt.ls.move_pos(val, self.comboBoxPos.currentText())
            self.ledPos.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        else:
            self.ledPos.setStyleSheet("QLabel {background-color : red; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")

    def set_spd(self):
        val = float(self.textEditSpd.toPlainText())
        if self.wt.calibrating == False and val > 0.0 and self.wt.discrete_sampling == False:
            self.wt.ls.set_speed(val, self.comboBoxSpd.currentText())
            self.ledSpd.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        else:
            self.ledSpd.setStyleSheet("QLabel {background-color : red; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")

    def move_dis(self):
        val = float(self.textEditDis.toPlainText())
        if self.wt.calibrating == False and val > 0.0 and self.wt.discrete_sampling == False:
            self.wt.ls.move_dis(val, self.comboBoxDis.currentText())
            self.ledDis.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        else:
            self.ledDis.setStyleSheet("QLabel {background-color : red; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")

    def set_dir(self):
        val = int(self.textEditDir.toPlainText())
        if self.wt.calibrating == False and val in [1,-1] and self.wt.discrete_sampling == False:
            self.wt.ls.set_dir(val)
            self.ledDir.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        else:
            self.ledDir.setStyleSheet("QLabel {background-color : red; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")

    def calibrate_sys(self):
        if self.wt.discrete_sampling == False:
            self.wt.calibrating = True

    def reset_sys(self):
        self.wt.calibrating = False
        self.wt.discrete_sampling = False
        self.wt.ls.reset_sys()

    def discrete_meas(self):
        if self.wt.calibrating == False:
            val_dis = float(self.textEditDiscreteDis.toPlainText())
            val_dis_unit = self.comboBoxDiscrete.currentText()
            val_time = float(self.textEditDiscreteTime.toPlainText())
            val_nr = float(self.textEditDiscreteNr.toPlainText())
            with_laser = self.checkBoxDiscreteLaser.isChecked()
            if val_dis > 0.0 and val_time > 0.0 and val_nr > 0.0:
                if with_laser == False:
                    self.ledDiscrete.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
                    self.wt.discrete_startup(val_dis, val_dis_unit, val_time, val_nr, with_laser)
                else:
                    if self.wt.laser_connected == True:
                        self.ledDiscrete.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
                        self.wt.discrete_startup(val_dis, val_dis_unit, val_time, val_nr, with_laser)
                    else:
                        self.ledDiscrete.setStyleSheet("QLabel {background-color : red; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
            else:
                self.ledDiscrete.setStyleSheet("QLabel {background-color : red; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        else:
            self.ledDiscrete.setStyleSheet("QLabel {background-color : red; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")


    def set_laser_rep_rate(self):
        rep_rates_kHz = {0:"  50.000 kHz", 1:" 100.000 kHz", 2:" 200.000 kHz", 3:" 299.625 kHz", 4:" 400.000 kHz", 5:" 500.000 kHz",
                                6:" 597.015 kHz", 7:" 707.965 kHz", 8:" 800.000 kHz", 9:" 898.876 kHz", 10:"1 000.000 kHz"}
        rep_rate = self.comboBoxLaserRep.currentText()
        for nr, value in rep_rates_kHz.items():
            if value == rep_rate:
                rep_rate_nr = nr
                self.wt.laser.set_repetition_rate(rep_rate_nr)

    def set_laser_energy(self):
        energy = float(self.textEditEnergy.toPlainText())
        unit = self.comboBoxLaserEnergy.currentText()
        print(energy, unit)
        self.wt.laser.set_pulse_energy(energy, unit)



# --------------------------------- Graph --------------------------------------


    def update_graph(self, abs_pos_mm):
        stage_len_mm = self.wt.ls.stage_length
        tray_length_mm = self.wt.ls.tray_length
        self.figure_ls.clear()
        plt.figure(num=1)
        ax = plt.axes(xlim=(0, stage_len_mm), ylim=(0, 30))
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)

        if self.wt.calibrated == True:
            rectangle = plt.Rectangle((stage_len_mm/2 - tray_length_mm/2 + abs_pos_mm, 0), tray_length_mm, 30, fc='lightblue')
            plt.gca().add_patch(rectangle)
        else:
            plt.text(0.5,0.5,'Calibrate the stage to see the absolute position',horizontalalignment='center', verticalalignment='center', transform = ax.transAxes)
        self.canvas_ls.draw()




if __name__ == '__main__':
    app=QApplication(sys.argv)
    ex=App()
    ex.show()
    sys.exit(app.exec_())
