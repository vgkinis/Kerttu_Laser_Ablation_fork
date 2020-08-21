from tkinter import *
import sys

class Interface: 
	
	def __init__(self, name):
		self.win = Tk() 
		self.name = name
		self.win.resizable(1,1)
		self.win.wm_title(name)
		self.working_dir = os.getcwd()
		self.canvas.draw()
		


if __name__ == 'main':
	app_name = "Laser Ablation"
	app = Interface(app_name)
	app.win.mainloop()
