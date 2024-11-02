import abc
import curses
import socket
import select
import threading
import time

from .display import Display
from .editor import Editor
from .basic import *

MSG_SYSTEM=1
MSG_USER=2
MSG_ADMIN=3
MSG_SELF=4
MSG_EXIT=5
MSG_GRANTED=6

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

		if self.height<4 or self.width<25:
			self.stdscr.addstr(0,0,"WINDOW SIZE TOO SMALL!",color(curses.COLOR_WHITE,curses.COLOR_RED)|curses.A_BOLD)
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
					if self.height>=4 and self.width>=25:
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
					if ret!='':
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

class ServerConsole(BaseConsole):
	def __init__(self,stdscr:curses.window,args):
		super().__init__(stdscr,args)

		self.clients:dict[str,socket.socket]={}
		self.clients_lock=threading.Lock()

	def broadcast(self,msg_type:int,msg_sender:str,msg:str,exclude:None|socket.socket=None):
		data=msg_type.to_bytes(1)+(msg_sender+'\0'+msg).encode()
		with self.clients_lock:
			for s in self.clients.values():
				if s==exclude:
					continue
				sendSocket(s,data)

		with self.window_lock:
			self.display.pushText(messageHeader(msg_type,msg_sender))
			self.display.pushText([msg,'\n'])
			self.refresh()

	def handleClient(self,client_socket:socket.socket,client_address):
		username=''
		joined=False
		try:
			if len(self.clients)+1==self.args.capacity:
				sendSocket(client_socket,"access denied: out of room capacity".encode())
				return
			sendSocket(client_socket,MSG_GRANTED.to_bytes(1))

			client_key=readSocket(client_socket)
			if client_key!=self.args.secretkey:
				sendSocket(client_socket,"access denied: incorrect password".encode())
				return
			sendSocket(client_socket,MSG_GRANTED.to_bytes(1))

			username=readSocket(client_socket).decode()
			with self.clients_lock:
				if username in self.clients or username==self.args.username:
					sendSocket(client_socket,"access denied: duplicated username".encode())
					return
				self.clients[username]=client_socket
			sendSocket(client_socket,MSG_GRANTED.to_bytes(1)+self.args.name.encode())

			joined=True
			self.broadcast(MSG_SYSTEM,"System",f"{username} has joined the room.",client_socket)

			while self.running:
				readable,_,_=select.select([client_socket],[],[],0.1)
				if readable:
					msg=readSocket(client_socket).decode()
					if not msg:
						break
					self.broadcast(MSG_USER,username,msg,client_socket)
		except:
			sendSocket(client_socket,MSG_EXIT.to_bytes(1))
		finally:
			if joined:
				with self.clients_lock:
					self.clients.pop(username)
				self.broadcast(MSG_SYSTEM,"System",f"{username} has left the room.",client_socket)

			client_socket.close()

	def serverLoop(self,server_socket:socket.socket):
		threads=[]
		try:
			server_socket.listen(5)
			while self.running:
				readable,_,_=select.select([server_socket],[],[],0.1)
				if readable:
					client_socket,client_address=server_socket.accept()
					thread=threading.Thread(target=self.handleClient,args=(client_socket,client_address))
					thread.start()
					threads.append(thread)

		except Exception as e:
			self.error_msg=', '.join(map(str,e.args))
		finally:
			self.running=False
			for thread in threads:
				thread.join()
			server_socket.close()

	def start(self):
		try:
			server_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
			server_socket.bind(('0.0.0.0',self.args.port))
			self.args.port=server_socket.getsockname()[1]

			with self.window_lock:
				self.display.pushText(messageHeader(MSG_SYSTEM,"System"))
				self.display.pushText([f"Room '{self.args.name}' has opened on port {self.args.port}."])
				self.display.pushText([])
				self.refresh()

			server_thread=threading.Thread(target=self.serverLoop,args=(server_socket,))
			server_thread.start()

			self.keyEventLoop()
			server_thread.join()

		except Exception as e:
			self.error_msg=', '.join(map(str,e.args))
		finally:
			self.running=False

	def sendMessage(self,msg:str):
		self.broadcast(MSG_ADMIN,self.args.username,msg)
		with self.window_lock:
			self.display.scrollDown(2**30)
			self.refresh()

class ClientConsole(BaseConsole):
	def __init__(self,stdscr:curses.window,args):
		super().__init__(stdscr,args)

		self.client_socket:socket.socket=socket.socket()
		self.window_lock=threading.Lock()

	def clientLoop(self,client_socket:socket.socket):
		try:
			while self.running:
				readable,_,_=select.select([client_socket],[],[],0.1)
				if readable:
					data=readSocket(client_socket)
					if not data or data[0]==MSG_EXIT:
						self.error_msg="room closed or unable to connect to host"
						return

					msg_sender,msg=data[1:].decode().split('\0')
					with self.window_lock:
						self.display.pushText(messageHeader(data[0],msg_sender))
						self.display.pushText([msg,'\n'])
						self.refresh()

		except Exception as e:
			self.error_msg=', '.join(map(str,e.args))
		finally:
			self.running=False
			client_socket.close()
	
	def start(self):
		try:
			client_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
			client_socket.connect(self.args.address)
			self.client_socket=client_socket

			res=readSocket(client_socket)
			if not res or res[0]!=MSG_GRANTED:
				self.error_msg=res.decode()
				return

			sendSocket(client_socket,self.args.secretkey)
			res=readSocket(client_socket)
			if not res or res[0]!=MSG_GRANTED:
				self.error_msg=res.decode()
				return

			sendSocket(client_socket,self.args.username.encode())
			res=readSocket(client_socket)
			if not res or res[0]!=MSG_GRANTED:
				self.error_msg=res.decode()
				return
			self.args.name=res[1:].decode()
			
			self.display.pushText(messageHeader(MSG_SYSTEM,"System"))
			self.display.pushText([f"You have joined the room '{self.args.name}' at {self.args.address[0]}:{self.args.address[1]}\n"])
			self.refresh()

			client_thread=threading.Thread(target=self.clientLoop,args=(client_socket,))
			client_thread.start()

			self.keyEventLoop()
			client_thread.join()

		except Exception as e:
			self.error_msg=', '.join(map(str,e.args))
		finally:
			self.running=False
	
	def sendMessage(self,msg:str):
		with self.window_lock:
			self.display.pushText(messageHeader(MSG_SELF,self.args.username))
			self.display.pushText([msg,'\n'])
			self.refresh()

		sendSocket(self.client_socket,msg.encode())
