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

from general_functions import *
import sys
import time
from general_functions import *
from datetime import datetime
from linear_stage import LinearStage
from serial.tools import list_ports
import functools
import schedule


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
        time.sleep(2)
        while True:
            try:
                if self.discrete_sampling == True:
                    if self.discrete_total > 0:
                        schedule.every(self.discrete_time).seconds.do(self.discrete_move)
                        self.discrete_total -= self.discrete_dis
                self.ls.ping_arduino()
                data_dict = self.ls.serial_read()
                self.motor_signals.emit(data_dict)
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

    def discrete_meas(self, dis_interval, dis_interval_unit, time_interval, total_dis, total_dis_unit):
        self.discrete_sampling = True
        self.discrete_dis = dis_interval
        self.discrete_dis_unit = dis_interval_unit
        self.discrete_time = time_interval
        self.discrete_total = total_dis
        self.discrete_total_unit = total_dis_unit

    def discrete_move(self):
        self.ls.move_dis(self.discrete_dis, self.discrete_dis_unit)

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
        #self.labelEvent.setStyleSheet("QLabel {font: Times New Roman; font-size: 12px}")
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

        discreteTxtLayout = QHBoxLayout()
        mainLayout.addLayout(discreteTxtLayout, 11, 0)
        discreteTxtLayout.setAlignment(Qt.AlignCenter)

        self.labelDiscrete1 = QLabel('Distance Interval', self)
        self.labelDiscrete1.setFixedSize(150, 34)
        discreteTxtLayout.addWidget(self.labelDiscrete1)
        discreteTxtLayout.addItem(QSpacerItem(80, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.labelDiscrete2 = QLabel('Time Interval', self)
        self.labelDiscrete2.setFixedSize(120, 34)
        discreteTxtLayout.addWidget(self.labelDiscrete2)
        discreteTxtLayout.addItem(QSpacerItem(80, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.labelDiscrete3 = QLabel('Total Distance', self)
        self.labelDiscrete3.setFixedSize(120, 34)
        discreteTxtLayout.addWidget(self.labelDiscrete3)

        discreteLayout = QHBoxLayout()
        mainLayout.addLayout(discreteLayout, 12, 0)
        discreteLayout.setAlignment(Qt.AlignCenter)

        self.textEditDiscreteDis = QTextEdit(self)
        self.textEditDiscreteDis.setFixedSize(88, 34)
        discreteLayout.addWidget(self.textEditDiscreteDis)
        discreteLayout.addItem(QSpacerItem(5, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.comboBoxDiscrete = QComboBox(self)
        self.comboBoxDiscrete.addItems(["mm", "steps", "rev"])
        self.comboBoxDiscrete.setFixedSize(88, 34)
        discreteLayout.addWidget(self.comboBoxDiscrete)
        discreteLayout.addItem(QSpacerItem(30, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.textEditDiscreteTime = QTextEdit(self)
        self.textEditDiscreteTime.setFixedSize(88, 34)
        discreteLayout.addWidget(self.textEditDiscreteTime)
        discreteLayout.addItem(QSpacerItem(5, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.labelDiscrete4 = QLabel('s', self)
        self.labelDiscrete4.setFixedSize(10, 34)
        discreteLayout.addWidget(self.labelDiscrete4)
        discreteLayout.addItem(QSpacerItem(30, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.textEditDiscreteTotal= QTextEdit(self)
        self.textEditDiscreteTotal.setFixedSize(88, 34)
        discreteLayout.addWidget(self.textEditDiscreteTotal)
        discreteLayout.addItem(QSpacerItem(5, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.comboBoxDiscreteTotal = QComboBox(self)
        self.comboBoxDiscreteTotal.addItems(["mm", "steps", "rev"])
        self.comboBoxDiscreteTotal.setFixedSize(88, 34)
        discreteLayout.addWidget(self.comboBoxDiscreteTotal)

        discreteStartLayout = QHBoxLayout()
        mainLayout.addLayout(discreteStartLayout, 13, 0)
        discreteStartLayout.setAlignment(Qt.AlignCenter)
        discreteStartLayout.addItem(horizontalSpacer2)

        self.pushButtonDiscrete = QPushButton('Start', self)
        self.pushButtonDiscrete.setFixedSize(88, 34)
        discreteStartLayout.addWidget(self.pushButtonDiscrete)
        discreteStartLayout.addItem(QSpacerItem(10, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.ledDiscrete = QLabel(self)
        self.ledDiscrete.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
        discreteStartLayout.addWidget(self.ledDiscrete)
        discreteStartLayout.addItem(horizontalSpacer2)
        discreteStartLayout.addItem(QSpacerItem(0, 100, QSizePolicy.Minimum, QSizePolicy.Expanding))


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

        if self.calibrating == True:
            self.wt.calibrate_sys()
            if data_dict["event_code"] == 1:
                self.calibrating = False
                self.calibrated = True

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
        val_dis = float(self.textEditDiscreteDis.toPlainText())
        val_dis_unit = self.comboBoxDiscrete
        val_time = float(self.textEditDiscreteTime.toPlainText())
        val_total_dis = float(self.textEditDiscreteTotal.toPlainText())
        val_total_dis_unit = self.comboBoxDiscreteTotal
        if self.calibrating == False and val_dis > 0.0 and val_time > 0.0 and val_total_dis > 0.0:
            self.discrete_sampling = True
            self.wt.discrete_meas(val_dis, val_dis_unit, val_time, val_total_dis, val_total_dis_unit)


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
