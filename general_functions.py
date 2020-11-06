from PyQt5.QtWidgets import QLCDNumber
from PyQt5.QtGui import QColor

def set_lcd_style(lcd):
    lcd.setSegmentStyle(QLCDNumber.Flat)
    palette1 = lcd.palette()
    palette1.setColor(palette1.WindowText, QColor(0, 0, 255))
    lcd.setPalette(palette1)
