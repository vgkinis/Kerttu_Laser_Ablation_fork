from PyQt5.QtWidgets import (QWidget, QPushButton, QTextEdit, QGridLayout, QComboBox, QHBoxLayout, QVBoxLayout, QApplication, QLCDNumber,
                             QLabel, QMainWindow, qApp, QSpacerItem, QSizePolicy, QFrame)
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
from datetime import datetime
from serial.tools import list_ports
import functools
import threading

from general_functions import *
from linear_stage import LinearStage


class WorkerThread(QThread):
    motor_signals = pyqtSignal(dict, name='motor_signals')
    def __init__(self, parent=None):
        QThread.__init__(self)

    def run(self):
        self.ls = LinearStage(json_path="linear_stage.json")
        self.ls.read_json()
        ports = (list(list_ports.comports()))
        port_name = list(map(lambda p : p["ttyACM" in p.device], ports))[0]
        serial_port = "/dev/" + port_name
        self.ls.start_serial(serial_port)
        self.discrete_sampling = False
        self.discrete_timer = None
        time.sleep(2)
        while True:
            try:
                self.ls.ping_arduino()
                data_dict = self.ls.serial_read()
                self.motor_signals.emit(data_dict)

                self.discrete_meas()
            except:
                continue

    def set_spd(self, val, unit):
        self.ls.set_speed(val, unit.currentText())

    def move_dis(self, val, unit):
        self.ls.move_dis(val, unit.currentText())

    def move_pos(self, val, unit):
        self.ls.move_pos(val, unit.currentText())

    def set_dir(self, val):
        self.ls.set_dir(val)

    def reset_sys(self):
        self.ls.reset_sys()

    def calibrate_sys(self):
        self.ls.calibrate_sys()

    def stop(self):
        #self.ser.close()
        print("stop")
        self.terminate()

    def discrete_startup(self, dis_interval, dis_interval_unit, time_interval, nr):
        self.discrete_sampling = True
        self.discrete_dis = dis_interval
        self.discrete_dis_unit = dis_interval_unit
        self.discrete_time = time_interval
        self.ls.set_event_code(4)
        self.ls.move_dis(self.discrete_dis, self.discrete_dis_unit)
        self.discrete_nr = nr-1

    def discrete_meas(self):
        if self.discrete_sampling == True:
            # Check if motor is moving
            if self.ls.dis_stp == 0:
                # Check if there are repetitons to do
                if self.discrete_nr > 0:
                    # Start the timer
                    if self.discrete_timer == None:
                        self.discrete_timer = time.time()
                    # Move the next distance interval if waiting time is over
                    if self.discrete_timer + self.discrete_time <= time.time():
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
        self.title='Motor control'
        self.left=10
        self.top=10
        self.width=720
        self.height=720
        self.setMinimumSize(720, 720)
        self.initUI()

    def initUI(self):

        self.calibrating = False
        self.calibrated = False
        self.discrete_sampling = False
        self.spd_mm_s = 5

        central = QWidget(self)

        mainLayout = QGridLayout(central)

        self.setWindowTitle(self.title)
        self.setGeometry(self.left,self.top,self.width,self.height)

        horizontalSpacer1 = QSpacerItem(88, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        horizontalSpacer2 = QSpacerItem(30, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        verticalSpacer1 = QSpacerItem(0, 120, QSizePolicy.Minimum, QSizePolicy.Expanding)
        verticalSpacer2 = QSpacerItem(0, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)


# ---------------------------------- Position ----------------------------------

        posLabelLayout = QHBoxLayout()
        mainLayout.addLayout(posLabelLayout, 0, 0)
        posLabelLayout.setAlignment(Qt.AlignLeft)
        posLabelLayout.addItem(horizontalSpacer2)

        self.labelPos = QLabel('Absolute Position', self)
        self.labelPos.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px}")
        posLabelLayout.addWidget(self.labelPos)

        posLayout = QHBoxLayout()
        mainLayout.addLayout(posLayout, 1, 0)
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
        mainLayout.addLayout(disLabelLayout, 2, 0)
        disLabelLayout.setAlignment(Qt.AlignLeft)
        disLabelLayout.addItem(horizontalSpacer2)

        self.labelDis = QLabel('Distance', self)
        self.labelDis.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px}")
        self.labelDis.setFixedSize(88, 34)
        disLabelLayout.addWidget(self.labelDis)

        disLayout = QHBoxLayout()
        mainLayout.addLayout(disLayout, 3, 0)
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
        mainLayout.addLayout(spdLabelLayout, 4, 0)
        spdLabelLayout.setAlignment(Qt.AlignLeft)
        spdLabelLayout.addItem(horizontalSpacer2)

        self.labelSpd = QLabel('Speed', self)
        self.labelSpd.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px}")
        self.labelSpd.setFixedSize(88, 34)
        spdLabelLayout.addWidget(self.labelSpd)

        spdLayout = QHBoxLayout()
        mainLayout.addLayout(spdLayout, 5, 0)
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
        mainLayout.addLayout(dirLabelLayout, 6, 0)
        dirLabelLayout.setAlignment(Qt.AlignLeft)
        dirLabelLayout.addItem(horizontalSpacer2)

        self.labelDir = QLabel('Direction', self)
        self.labelDir.setStyleSheet("QLabel {font: Times New Roman; font-size: 15px}")
        self.labelDir.setFixedSize(111, 34)
        dirLabelLayout.addWidget(self.labelDir)

        dirLayout = QHBoxLayout()
        mainLayout.addLayout(dirLayout, 7, 0)
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


# --------------------------------- Varia --------------------------------------
        variaLayout = QHBoxLayout()

        mainLayout.addLayout(variaLayout, 8, 0)
        variaLayout.setAlignment(Qt.AlignLeft)
        variaLayout.addItem(verticalSpacer1)
        variaLayout.addItem(horizontalSpacer2)

        self.pushButtonC = QPushButton('Calibrate', self)
        self.pushButtonC.setFixedSize(88, 34)
        variaLayout.addWidget(self.pushButtonC)
        variaLayout.addItem(horizontalSpacer2)

        self.pushButtonR = QPushButton('Reset', self)
        self.pushButtonR.setFixedSize(88, 34)
        variaLayout.addWidget(self.pushButtonR)
        variaLayout.addItem(QSpacerItem(128, 34, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.labelEvent = QLabel('Event Code', self)
        variaLayout.addWidget(self.labelEvent)
        variaLayout.addItem(QSpacerItem(10, 34, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.lcdNumberEvent = QLCDNumber(self)
        self.lcdNumberEvent.setFixedSize(100, 34)
        set_lcd_style(self.lcdNumberEvent)
        variaLayout.addWidget(self.lcdNumberEvent)

        variaLayout.addItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

# --------------------------------- Graph --------------------------------------

        graphLayout = QHBoxLayout()
        mainLayout.addLayout(graphLayout, 9, 0)

        self.figure_ls = plt.figure()
        self.figure_ls.set_figheight(0.5)
        self.figure_ls.set_figwidth(5)
        self.canvas_ls = FigureCanvas(self.figure_ls)

        graphLayout.addWidget(self.canvas_ls)

        variaLayout.addItem(QSpacerItem(0, 100, QSizePolicy.Minimum, QSizePolicy.Expanding))


# --------------------------- Discrete movement --------------------------------

        discreteLabelLayout = QHBoxLayout()
        mainLayout.addLayout(discreteLabelLayout, 10, 0)
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

        discrete1Layout = QHBoxLayout()
        mainLayout.addLayout(discrete1Layout, 11, 0)
        discrete1Layout.setAlignment(Qt.AlignCenter)

        discrete1Layout.addWidget(self.labelDiscrete1)

        self.textEditDiscreteDis = QTextEdit(self)
        self.textEditDiscreteDis.setFixedSize(80, 34)
        discrete1Layout.addWidget(self.textEditDiscreteDis)

        self.comboBoxDiscrete = QComboBox(self)
        self.comboBoxDiscrete.addItems(["mm", "steps", "rev"])
        self.comboBoxDiscrete.setFixedSize(65, 34)
        discrete1Layout.addWidget(self.comboBoxDiscrete)

        add_custom_spacer(20,34,discrete1Layout)
        discrete1Layout.addWidget(self.labelDiscrete2)

        self.textEditDiscreteTime = QTextEdit(self)
        self.textEditDiscreteTime.setFixedSize(80, 34)
        discrete1Layout.addWidget(self.textEditDiscreteTime)

        self.labelDiscrete5 = QLabel('s', self)
        self.labelDiscrete5.setFixedSize(10, 34)
        discrete1Layout.addWidget(self.labelDiscrete5)

        add_custom_spacer(20,34,discrete1Layout)
        discrete1Layout.addWidget(self.labelDiscrete3)

        self.textEditDiscreteNr = QTextEdit(self)
        self.textEditDiscreteNr.setFixedSize(80, 34)
        discrete1Layout.addWidget(self.textEditDiscreteNr)

        discrete2Layout = QHBoxLayout()
        mainLayout.addLayout(discrete2Layout, 12, 0)
        discrete2Layout.setAlignment(Qt.AlignCenter)

        self.pushButtonDiscrete = QPushButton('Start', self)
        self.pushButtonDiscrete.setFixedSize(88, 34)
        discrete2Layout.addWidget(self.pushButtonDiscrete)

        self.ledDiscrete = QLabel(self)
        self.ledDiscrete.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        discrete2Layout.addWidget(self.ledDiscrete)
        discrete2Layout.addItem(horizontalSpacer2)
        discrete2Layout.addItem(QSpacerItem(0, 80, QSizePolicy.Minimum, QSizePolicy.Expanding))


# -----------------------------------------------------------------------------
        self.wt=WorkerThread() # This is the thread object
        self.wt.start()
        self.wt.motor_signals.connect(self.slot_method)
        self.pushButtonPos.clicked.connect(functools.partial(self.move_pos))
        self.pushButtonSpd.clicked.connect(functools.partial(self.set_spd))
        self.pushButtonDir.clicked.connect(functools.partial(self.set_dir))
        self.pushButtonDis.clicked.connect(functools.partial(self.move_dis))
        self.pushButtonR.clicked.connect(functools.partial(self.reset_sys))
        self.pushButtonC.clicked.connect(functools.partial(self.calibrate_sys))
        self.pushButtonDiscrete.clicked.connect(functools.partial(self.discrete_meas))

        app.aboutToQuit.connect(QApplication.instance().quit) #to stop the thread when closing the GUI


    def slot_method(self, data_dict):
        self.lcdNumberPos.display(data_dict["pos_" + self.comboBoxPosFb.currentText()])
        self.lcdNumberDis.display(data_dict["dis_" + self.comboBoxDisFb.currentText()])
        self.lcdNumberSpd.display(data_dict["spd_" + self.comboBoxSpdFb.currentText()])
        self.lcdNumberDir.display(data_dict["direction"])
        self.lcdNumberEvent.display(data_dict["event_code"])

        self.spd_mm_s = data_dict["spd_mm/s"]

        if self.calibrating == True:
            self.wt.calibrate_sys()
            if data_dict["event_code"] == 1:
                self.calibrating = False
                self.calibrated = True

        if self.discrete_sampling == True:
            if data_dict["event_code"] == 0:
                self.discrete_sampling = False

        abs_pos_mm = data_dict["pos_mm"]

        self.update_graph(abs_pos_mm)

    def move_pos(self):
        val = float(self.textEditPos.toPlainText())
        if self.calibrating == False and self.discrete_sampling == False:
            self.wt.move_pos(val, self.comboBoxPos)
            self.ledPos.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        else:
            self.ledPos.setStyleSheet("QLabel {background-color : red; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")

    def set_spd(self):
        val = float(self.textEditSpd.toPlainText())
        if self.calibrating == False and val > 0.0 and self.discrete_sampling == False:
            self.wt.set_spd(val, self.comboBoxSpd)
            self.ledSpd.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        else:
            self.ledSpd.setStyleSheet("QLabel {background-color : red; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")

    def move_dis(self):
        val = float(self.textEditDis.toPlainText())
        if self.calibrating == False and val > 0.0 and self.discrete_sampling == False:
            self.wt.move_dis(val, self.comboBoxDis)
            self.ledDis.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        else:
            self.ledDis.setStyleSheet("QLabel {background-color : red; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")

    def set_dir(self):
        val = float(self.textEditDir.toPlainText())
        if self.calibrating == False and val in [1,-1] and self.discrete_sampling == False:
            self.wt.set_dir(val)
            self.ledDir.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        else:
            self.ledDir.setStyleSheet("QLabel {background-color : red; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")

    def calibrate_sys(self):
        if self.discrete_sampling == False:
            self.calibrating = True

    def reset_sys(self):
        self.calibrating = False
        self.wt.reset_sys()

    def discrete_meas(self):
        if self.calibrating == False:
            val_dis = float(self.textEditDiscreteDis.toPlainText())
            val_dis_unit = self.comboBoxDiscrete.currentText()
            val_time = float(self.textEditDiscreteTime.toPlainText())
            val_nr = float(self.textEditDiscreteNr.toPlainText())
            if self.calibrating == False and val_dis > 0.0 and val_time > 0.0 and val_nr > 0.0:
                self.discrete_sampling = True
                self.ledDiscrete.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
                self.wt.discrete_startup(val_dis, val_dis_unit, val_time, val_nr)
            else:
                self.ledDiscrete.setStyleSheet("QLabel {background-color : red; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        else:
            self.ledDiscrete.setStyleSheet("QLabel {background-color : red; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")



# --------------------------------- Graph --------------------------------------


    def update_graph(self, abs_pos_mm):
        # TODO : to not hard-coded value in the future
        stage_len_mm = 1200
        self.figure_ls.clear()
        plt.figure(num=1)
        ax = plt.axes(xlim=(0, 1200), ylim=(0, 30))
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)

        if self.calibrated == True:
            rectangle = plt.Rectangle((stage_len_mm/2 - 550/2 + abs_pos_mm, 0), 550, 30, fc='lightblue')
            plt.gca().add_patch(rectangle)
        else:
            plt.text(0.5,0.5,'Calibrate the stage to see the absolute position',horizontalalignment='center', verticalalignment='center', transform = ax.transAxes)
        self.canvas_ls.draw()




if __name__ == '__main__':
    app=QApplication(sys.argv)
    ex=App()
    ex.show()
    sys.exit(app.exec_())
