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


def turn_led_on_off(led, checked):
    if checked:
        led.setStyleSheet("QLabel {background-color : forestgreen; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
    else:
        led.setStyleSheet("QLabel {background-color : whitesmoke; border-color : black; border-width : 2px; border-style : solid; border-radius : 10px; min-height: 18px; min-width: 18px; max-height: 18px; max-width:18px}")
