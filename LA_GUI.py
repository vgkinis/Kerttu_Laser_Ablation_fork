from PyQt5.QtWidgets import QApplication,QWidget,QPushButton, QTextEdit, QComboBox, QLCDNumber, QLabel
from PyQt5.QtCore import pyqtSlot, QRect, QThread, pyqtSignal
from PyQt5.QtGui import QColor
import functools
import sys
from general_functions import *
from datetime import datetime
from linear_stage import LinearStage
from serial.tools import list_ports

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
        # time.sleep(2)
        while True:
            try:
                data_dict = self.ls.serial_read()
                self.motor_signals.emit(data_dict)
            except:
                continue


    def set_spd(self, val, unit):
        self.ls.set_speed(val.toPlainText(), unit.currentText())

    def move_dis(self, val, unit):
        self.ls.move_dis(val.toPlainText(), unit.currentText())

    def set_dir(self, val):
        self.ls.set_dir(val.toPlainText())

    def stop(self):
        #self.ser.close()
        print("stop")
        self.terminate()



class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title='Motor control'
        self.left=10
        self.top=10
        self.width=700
        self.height=600
        self.initUI()


    def initUI(self):
        x_coords = [40, 160, 280, 420, 550]
        y_coords = [30, 70, 130, 170, 230, 270, 340, 380, 450, 490]

        self.setWindowTitle(self.title)
        self.setGeometry(self.left,self.top,self.width,self.height)

        self.labelPos = QLabel('Absolute position', self)
        self.labelPos.setGeometry(QRect(x_coords[0], y_coords[0], 111, 34))

        self.labelDis = QLabel('Distance', self)
        self.labelDis.setGeometry(QRect(x_coords[0], y_coords[2], 111, 34))

        self.labelSpd = QLabel('Speed', self)
        self.labelSpd.setGeometry(QRect(x_coords[0], y_coords[4], 111, 34))

        self.labelDir = QLabel('Direction', self)
        self.labelDir.setGeometry(QRect(x_coords[0], y_coords[6], 111, 34))

        self.textEditPos = QTextEdit(self)
        self.textEditPos.setGeometry(QRect(x_coords[0], y_coords[1], 88, 34))

        self.textEditDis = QTextEdit(self)
        self.textEditDis.setGeometry(QRect(x_coords[0], y_coords[3], 88, 34))

        self.textEditSpd = QTextEdit(self)
        self.textEditSpd.setGeometry(QRect(x_coords[0], y_coords[5], 88, 34))

        self.textEditDir = QTextEdit(self)
        self.textEditDir.setGeometry(QRect(x_coords[0], y_coords[7], 88, 34))


        self.comboBoxPos = QComboBox(self)
        self.comboBoxPos.addItems(["mm", "steps", "rev"])
        self.comboBoxPos.setGeometry(QRect(x_coords[1], y_coords[1], 88, 34))

        self.comboBoxDis = QComboBox(self)
        self.comboBoxDis.addItems(["mm", "steps", "rev"])
        self.comboBoxDis.setGeometry(QRect(x_coords[1], y_coords[3], 88, 34))

        self.comboBoxSpd = QComboBox(self)
        self.comboBoxSpd.addItems(["mm/s", "step/s", "rev/s", "us/step"])
        self.comboBoxSpd.setGeometry(QRect(x_coords[1], y_coords[5], 88, 34))

        self.comboBoxPosFb = QComboBox(self)
        self.comboBoxPosFb.addItems(["mm", "steps", "rev"])
        self.comboBoxPosFb.setGeometry(QRect(x_coords[4], y_coords[1], 88, 34))

        self.comboBoxDisFb = QComboBox(self)
        self.comboBoxDisFb.addItems(["mm", "steps", "rev"])
        self.comboBoxDisFb.setGeometry(QRect(x_coords[4], y_coords[3], 88, 34))

        self.comboBoxSpdFb = QComboBox(self)
        self.comboBoxSpdFb.addItems(["mm/s", "step/s", "rev/s", "us/step"])
        self.comboBoxSpdFb.setGeometry(QRect(x_coords[4], y_coords[5], 88, 34))


        self.pushButtonPos = QPushButton('Move', self)
        self.pushButtonPos.setGeometry(QRect(x_coords[2], y_coords[1], 88, 34))

        self.pushButtonDis = QPushButton('Move', self)
        self.pushButtonDis.setGeometry(QRect(x_coords[2], y_coords[3], 88, 34))

        self.pushButtonSpd = QPushButton('Set', self)
        self.pushButtonSpd.setGeometry(QRect(x_coords[2], y_coords[5], 88, 34))

        self.pushButtonDir = QPushButton('Set', self)
        self.pushButtonDir.setGeometry(QRect(x_coords[2], y_coords[7], 88, 34))

        self.pushButtonP = QPushButton('Pause', self)
        self.pushButtonP.setGeometry(QRect(x_coords[0], y_coords[9], 88, 34))

        self.pushButtonR = QPushButton('Reset', self)
        self.pushButtonR.setGeometry(QRect(x_coords[1], y_coords[9], 88, 34))

        self.lcdNumberPos = QLCDNumber(self)
        self.lcdNumberPos.setGeometry(QRect(x_coords[3], y_coords[1],  100, 34))
        set_lcd_style(self.lcdNumberPos)

        self.lcdNumberDis = QLCDNumber(self)
        self.lcdNumberDis.setGeometry(QRect(x_coords[3], y_coords[3],  100, 34))
        set_lcd_style(self.lcdNumberDis)

        self.lcdNumberSpd = QLCDNumber(self)
        self.lcdNumberSpd.setGeometry(QRect(x_coords[3], y_coords[5],  100, 34))
        set_lcd_style(self.lcdNumberSpd)

        self.lcdNumberDir = QLCDNumber(self)
        self.lcdNumberDir.setGeometry(QRect(x_coords[3], y_coords[7],  100, 34))
        set_lcd_style(self.lcdNumberDir)

        self.wt=WorkerThread() # This is the thread object
        self.wt.start()
        self.wt.motor_signals.connect(self.slot_method)
        self.pushButtonSpd.clicked.connect(functools.partial(self.wt.set_spd, self.textEditSpd, self.comboBoxSpd))
        self.pushButtonDir.clicked.connect(functools.partial(self.wt.set_dir, self.textEditDir))
        self.pushButtonDis.clicked.connect(functools.partial(self.wt.move_dis, self.textEditDis, self.comboBoxDis))

        app.aboutToQuit.connect(QApplication.instance().quit) #to stop the thread when closing the GUI


    def slot_method(self, data_dict):
        self.lcdNumberPos.display(data_dict["pos_" + self.comboBoxPosFb.currentText()])
        self.lcdNumberDis.display(data_dict["dis_" + self.comboBoxDisFb.currentText()])
        self.lcdNumberSpd.display(data_dict["spd_" + self.comboBoxSpdFb.currentText()])
        self.lcdNumberDir.display(data_dict["direction"])



if __name__=='__main__':
    app=QApplication(sys.argv)
    ex=App()
    ex.show()
    sys.exit(app.exec_())
