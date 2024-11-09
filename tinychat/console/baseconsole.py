import abc
import curses
import socket
import select
import threading
import time

from ..display import *
from ..editor import *
from ..basic.network import *
from ..basic.graphics import *

def messageHeader(msg_type:int,msg_sender:str):
	time_str=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
	ret=[curses.A_BOLD,msg_sender,color(curses.COLOR_CYAN,curses.COLOR_BLACK),' ',time_str]
	if msg_type==MSG_SYSTEM:
		ret[0]|=color(curses.COLOR_MAGENTA,curses.COLOR_BLACK)
	elif msg_type==MSG_USER:
		ret[0]|=color(curses.COLOR_YELLOW,curses.COLOR_BLACK)
	elif msg_type==MSG_ADMIN:
		ret[0]|=color(curses.COLOR_RED,curses.COLOR_BLACK)
	elif msg_type==MSG_SELF:
		ret[0]|=color(curses.COLOR_GREEN,curses.COLOR_BLACK)
	return ret

class BaseConsole:
	def __init__(self,stdscr:curses.window,args):
		self.stdscr=stdscr
		self.args=args

		self.height,self.width=stdscr.getmaxyx()
		self.editor=Editor(stdscr,self.height,0,self.height//2,self.width)
		self.display=Display(stdscr,1,1,self.height-1,self.width-2)
		self.in_edit_mode=False
		self.running=True
		self.error_msg=None

		self.window_lock=threading.Lock()

	def refresh(self):
		self.stdscr.erase()

		if self.height<4:
			self.stdscr.addstr(0,0,"WINDOW SIZE TOO SMALL!"[:min(self.width,22)-1],color(curses.COLOR_WHITE,curses.COLOR_RED)|curses.A_BOLD)
		else:
			extra=2 if self.display.new_message else 0
			title=self.args.name
			if len(title)+extra>self.width-2:
				title=title[:self.width-6-extra]+'...'
			pos=(self.width-len(title)-extra)//2
			self.stdscr.addstr(0,pos+extra,title,curses.A_BOLD)
			if extra:
				self.stdscr.addch(0,pos,'●',color(curses.COLOR_RED,curses.COLOR_BLACK)|curses.A_BOLD)

			if self.in_edit_mode:
				self.display.resize(self.height-min(self.editor.height,self.editor.pad.getmaxyx()[0])-2,-1)
				self.editor.update()
			else:
				self.display.resize(self.height-1,-1)
			self.display.update()			
	
		self.stdscr.refresh()

	def keyEventLoop(self):
		self.stdscr.timeout(50)
		while self.running:
			try:
				key=self.stdscr.get_wch()
			except curses.error:
				continue

			if key==curses.KEY_RESIZE:
				self.height,self.width=self.stdscr.getmaxyx()
				with self.window_lock:
					if self.height>=4:
						self.editor.resize(self.height//2-1,self.width)
						self.editor.move(self.height,0)
						self.display.resize(self.height-1,self.width-2)
						self.display.move(1,1)
					self.refresh()

			elif self.in_edit_mode and key!=curses.KEY_MOUSE:
				ret=self.editor.sendKey(key)
				if isinstance(ret,str):
					self.in_edit_mode=False
					curses.curs_set(0)
					if ret:
						if self.editor.prompt==':':
							self.sendMessage(ret)
						else:
							self.sendCommand(ret)
				self.refresh()

			elif key==':' or key=='：':
				self.in_edit_mode=True
				self.editor.initEditor(':')
				self.refresh()
				curses.curs_set(1)
			
			elif key=='/':
				self.in_edit_mode=True
				self.editor.initEditor('/')
				self.refresh()
				curses.curs_set(1)

			else:
				self.display.sendKey(key)
				self.refresh()


	@abc.abstractmethod
	def start(self)->str|None:...

	@abc.abstractmethod
	def sendMessage(self,msg:str):...

	@abc.abstractmethod
	def sendCommand(self,cmd:str):
		if cmd=="quit":
			self.running=False
