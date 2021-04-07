from PyQt5.QtWidgets import QLCDNumber, QLabel
from PyQt5.QtGui import QColor

def set_lcd_style(lcd):
    lcd.setSegmentStyle(QLCDNumber.Flat)
    palette1 = lcd.palette()
    palette1.setColor(palette1.WindowText, QColor(0, 0, 255))
    lcd.setPalette(palette1)


def add_custom_spacer(x,y,layout):
    spacer = QLabel('')
    spacer.setFixedSize(x, y)
    layout.addWidget(spacer)
