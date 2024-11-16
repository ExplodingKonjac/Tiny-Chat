import time
import threading

from ..basic.settings import *
from ..basic.graphics import *
from ..chatcore import *
from .editor import *
from .textbox import *

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

class MainWindow:
	def __init__(self,stdscr:curses.window,CoreType:type[BaseCore])->None:
		self._stdscr=stdscr
	
		self._height,self._width=stdscr.getmaxyx()
		self._editor=Editor(stdscr,self._height,0,self._height//2,self._width)
		self._textbox=Textbox(stdscr,1,1,self._height-1,self._width-2)
		self._window_lock=threading.Lock()

		self._edit_mode=0 # 0: not, 1: msg, 2: cmd
		self._running=True

		self._core=CoreType(
			on_new_message=self._showMessage,
			on_join_room=self._showJoinRoom,
			on_left_room=self._leftRoom,
			on_new_user=self._showNewUser,
			on_user_left=self._showUserLeft
		)
		self._core.start()

	def _showMessage(self,msg_type:int,msg_sender:str,msg_text:str):
		with self._window_lock:
			self._textbox.pushText(messageHeader(msg_type,msg_sender))
			self._textbox.pushText([msg_text,'\n'])
			self.refresh()
	
	def _showJoinRoom(self,address:tuple[str,int],title:str):
		with self._window_lock:
			self._textbox.pushText(messageHeader(MSG_SYSTEM,"System"))
			if type(self._core)==ServerCore:
				self._textbox.pushText([f"Room '{title}' has opened on port {address[1]}.\n"])
			else:
				self._textbox.pushText([f"You have joined the room '{title}' at {address[0]}:{address[1]}\n"])
			self.refresh()
	
	def _leftRoom(self):
		self._running=False
	
	def _showNewUser(self,address:tuple[str,int],username:str):
		with self._window_lock:
			self._textbox.pushText(messageHeader(MSG_SYSTEM,"System"))
			self._textbox.pushText([f"{username} has joined the room.\n"])
			self.refresh()
	
	def _showUserLeft(self,username:str,kicked:bool):
		with self._window_lock:
			self._textbox.pushText(messageHeader(MSG_SYSTEM,"System"))
			self._textbox.pushText([f"{username} has {"been kicked by host" if kicked else "left the room"}.\n"])
			self.refresh()

	def _processCommand(self,cmd:str):
		argv=cmd.split()
		output=[]

		try:
			if argv[0]=="quit":
				if len(argv)!=1:
					raise Exception("usage: /quit")

				self._core.terminate()
				self._running=False
			
			elif argv[0]=="list":
				if len(argv)!=1:
					raise Exception("usage: /list")

				userlist=self._core.queryUserList()
				output.append("Current online users:")
				for user in userlist:
					output.append(' * '+user)

			elif argv[0]=="kick":
				if type(self._core)!=ServerCore:
					raise Exception("only the host could execude 'kick' command")

				if len(argv)!=2:
					raise Exception("usage: /kick USERNAME")

				assert(type(self._core)==ServerCore)
				self._core.kick(argv[1])
				output.append(f"Successfully kicked '{argv[1]}'")

			else:
				raise Exception(f"unknown command '{argv[0]}'")

		except Exception as e:
			output=[f"error: {", ".join(e.args)}"]

		finally:
			if output:
				with self._window_lock:
					self._textbox.pushText(messageHeader(MSG_SYSTEM,"Command Output"))
					for line in output:
						self._textbox.pushText([line])
					self._textbox.pushText([])

	def refresh(self):
		self._stdscr.erase()

		if self._height<4:
			self._stdscr.addstr(0,0,"WINDOW SIZE TOO SMALL!"[:self._width],color(curses.COLOR_WHITE,curses.COLOR_RED)|curses.A_BOLD)
		else:
			extra=2 if self._textbox._new_text else 0
			title=args().title
			if len(title)+extra>self._width-2:
				title=title[:self._width-5-extra]+'...'
			pos=(self._width-len(title)-extra)//2

			if extra:
				self._stdscr.addch(0,pos,'●',color(curses.COLOR_RED,curses.COLOR_BLACK)|curses.A_BOLD)
			self._stdscr.addstr(0,pos+extra,title,curses.A_BOLD)

			if self._edit_mode:
				self._textbox.resize(self._height-self._editor.actual_height-2,-1)
				self._editor.update()
				self._textbox.update()
			else:
				self._textbox.resize(self._height-1,-1)
				self._textbox.update()
	
		self._stdscr.refresh()

	def main(self):
		self._stdscr.timeout(50)
		self.refresh()
		while self._running and self._core.running:
			try:
				key=self._stdscr.get_wch()
			except curses.error:
				continue

			if key==curses.KEY_RESIZE:
				self._height,self._width=self._stdscr.getmaxyx()
				with self._window_lock:
					if self._height>=4:
						self._editor.resize(self._height//2-1,self._width)
						self._editor.move(self._height,0)
						self._textbox.resize(self._height-1,self._width-2)
						self._textbox.move(1,1)
					self.refresh()

			elif self._edit_mode and key!=curses.KEY_MOUSE:
				ret=self._editor.sendKey(key)
				if isinstance(ret,str):
					curses.curs_set(0)
					if ret:
						if self._edit_mode==1:
							self._core.sendMessage(ret)
						else:
							self._processCommand(ret)
					self._edit_mode=0

				with self._window_lock:
					self.refresh()

			elif key==':' or key=='：':
				self._edit_mode=1
				self._editor.initEditor(':')
				curses.curs_set(1)

				with self._window_lock:
					self.refresh()
			
			elif key=='/':
				self._edit_mode=2
				self._editor.initEditor('/')
				curses.curs_set(1)

				with self._window_lock:
					self.refresh()

			else:
				self._textbox.sendKey(key)

				with self._window_lock:
					self.refresh()
		
		return self._core.error_msg