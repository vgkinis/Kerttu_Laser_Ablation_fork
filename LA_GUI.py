from PyQt5.QtWidgets import QApplication,QWidget,QPushButton, QTextEdit, QComboBox, QLCDNumber, QLabel
from PyQt5.QtCore import pyqtSlot, QRect, QThread, pyqtSignal
from PyQt5.QtGui import QColor
import functools
import sys
from general_functions import *
from datetime import datetime

class WorkerThread(QThread):
    motor_signals = pyqtSignal(float, float, int, name='motor_signals')
    def __init__(self, parent=None):
        QThread.__init__(self)
        
    def run(self):
        while True:
            t_now = datetime.now()
            self.motor_signals.emit(float(t_now.hour), float(t_now.minute), int(t_now.second))
            
        
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
        self.width=640
        self.height=600
        self.initUI()
        
        
    def initUI(self):
        x_coords = [40, 160, 280, 420]
        y_coords = [30, 70, 130, 170, 230, 270, 340, 380, 450, 490]
        
        self.setWindowTitle(self.title)
        self.setGeometry(self.left,self.top,self.width,self.height)
        
        self.label1 = QLabel('Absolute position', self)
        self.label1.setGeometry(QRect(x_coords[0], y_coords[0], 111, 34))
        
        self.label2 = QLabel('Speed', self)
        self.label2.setGeometry(QRect(x_coords[0], y_coords[2], 111, 34))
        
        self.label3 = QLabel('Direction', self)
        self.label3.setGeometry(QRect(x_coords[0], y_coords[4], 111, 34))
        
        self.textEdit1 = QTextEdit(self)
        self.textEdit1.setGeometry(QRect(x_coords[0], y_coords[1], 88, 34))
        
        self.textEdit2 = QTextEdit(self)
        self.textEdit2.setGeometry(QRect(x_coords[0], y_coords[3], 88, 34))
        
        self.textEdit3 = QTextEdit(self)
        self.textEdit3.setGeometry(QRect(x_coords[0], y_coords[5], 88, 34))
        
        
        self.comboBox1 = QComboBox(self)
        self.comboBox1.addItem("mm")
        self.comboBox1.addItem("steps")
        self.comboBox1.addItem("rev")
        self.comboBox1.setGeometry(QRect(x_coords[1], y_coords[1], 88, 34))
        
        
        self.comboBox2 = QComboBox(self)
        self.comboBox2.addItem("mm/s")
        self.comboBox2.addItem("steps/s")
        self.comboBox2.addItem("rev/s")
        self.comboBox2.setGeometry(QRect(x_coords[1], y_coords[3], 88, 34))
        
        
        self.pushButton_1 = QPushButton('Send', self)
        self.pushButton_1.setGeometry(QRect(x_coords[2], y_coords[1], 88, 34))
        #self.pushButton_1.clicked.connect(functools.partial(self.check_inputs, 1))
        
        self.pushButton_2 = QPushButton('Send', self)
        self.pushButton_2.setGeometry(QRect(x_coords[2], y_coords[3], 88, 34))
        #self.pushButton_2.clicked.connect(functools.partial(self.check_inputs, 2))
        
        self.pushButton_3 = QPushButton('Send', self)
        self.pushButton_3.setGeometry(QRect(x_coords[2], y_coords[5], 88, 34))
        #self.pushButton_3.clicked.connect(functools.partial(self.check_inputs, 3))
        
        self.pushButton_4 = QPushButton('Pause', self)
        self.pushButton_4.setGeometry(QRect(x_coords[0], y_coords[9], 88, 34))
        
        self.pushButton_5 = QPushButton('Reset', self)
        self.pushButton_5.setGeometry(QRect(x_coords[1], y_coords[9], 88, 34))
        
        self.lcdNumber1 = QLCDNumber(self)
        self.lcdNumber1.setGeometry(QRect(x_coords[3], y_coords[1],  100, 34))
        set_lcd_style(self.lcdNumber1)
        
        self.lcdNumber2 = QLCDNumber(self)
        self.lcdNumber2.setGeometry(QRect(x_coords[3], y_coords[3],  100, 34))
        set_lcd_style(self.lcdNumber2)
        
        self.lcdNumber3 = QLCDNumber(self)
        self.lcdNumber3.setGeometry(QRect(x_coords[3], y_coords[5],  100, 34))
        set_lcd_style(self.lcdNumber3)
      
        self.wt=WorkerThread() # This is the thread object
        self.wt.start()
        self.wt.motor_signals.connect(self.slot_method) 
        app.aboutToQuit.connect(QApplication.instance().quit) #to stop the thread when closing the GUI
        
        
    def check_inputs(self, nr):
        print(nr)
        self.lcdNumber1.display(self.textEdit1.toPlainText())
        
        
    def slot_method(self, pos, speed, direction):
        self.lcdNumber1.display(pos)
        self.lcdNumber2.display(speed)
        self.lcdNumber3.display(direction)
        
        
        
if __name__=='__main__':
    app=QApplication(sys.argv)
    ex=App()
    ex.show()
    sys.exit(app.exec_())
