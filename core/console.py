import curses
from .display import Display
from .editor import Editor
from .basic import *

class Console:
	def __init__(self,stdscr:curses.window,height:int,width:int):
		self.stdscr=stdscr
		self.height=height
		self.width=width
		self.editor=Editor(stdscr,height,0,height//2,width)
		self.display=Display(stdscr,1,1,height-1,width-2)
		self.in_edit_mode=False
		self.size_too_small=(height<4)
		self.refresh()
	
	def refresh(self):
		self.stdscr.erase()
		if self.size_too_small:
			self.stdscr.addstr(0,0,"WINDOW SIZE TOO SMALL!",colorAttr(curses.COLOR_WHITE,curses.COLOR_RED)|curses.A_BOLD)
		elif self.in_edit_mode:
			self.display.resize(self.height-min(self.editor.height,self.editor.pad.getmaxyx()[0])-2,-1)
			self.display.update()
			self.editor.update()
		else:
			self.display.resize(self.height-1,-1)
			self.display.update()
		self.stdscr.refresh()

	def keyEventLoop(self):
		while True:
			key=self.stdscr.get_wch()
			if key==curses.KEY_RESIZE:
				self.height,self.width=self.stdscr.getmaxyx()
				self.size_too_small=(self.height<4)
				if not self.size_too_small:
					self.editor.resize(self.height//2,self.width)
					self.editor.move(self.height,0)
					self.display.resize(self.height-1,self.width-2)
					self.display.move(1,1)
				self.refresh()
			elif key==curses.KEY_MOUSE:
				self.display.sendKey(key)
				self.refresh()
			elif self.in_edit_mode:
				ret=self.editor.sendKey(key)
				if isinstance(ret,str):
					self.in_edit_mode=False
					curses.curs_set(0)
					if ret!='':
						self.display.pushText([ret])
						self.display.scrollDown(10**9)
				self.refresh()
			elif key in (':','/'):
				self.in_edit_mode=True
				self.editor.initEditor(key)
				self.refresh()
				curses.curs_set(1)
			elif key=='q':
				break
			else:
				self.display.sendKey(key)
				self.refresh()
