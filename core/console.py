import abc
import curses
import socket
import select
import threading
import time
import hashlib
import getpass

from .display import Display
from .editor import Editor
from .basic import *

MSG_SYSTEM=1
MSG_USER=2
MSG_ADMIN=3
MSG_EXIT=4

def messageHeader(msg_type:int,msg_sender:str):
	time_str=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
	ret=[0,msg_sender,color(curses.COLOR_CYAN,curses.COLOR_BLACK),time_str]
	if msg_type==MSG_SYSTEM:
		ret[0]=color(curses.COLOR_GREEN,curses.COLOR_BLACK)
	elif msg_type==MSG_USER:
		ret[0]=color(curses.COLOR_YELLOW,curses.COLOR_BLACK)
	elif msg_type==MSG_ADMIN:
		ret[0]=color(curses.COLOR_RED,curses.COLOR_BLACK)
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
		self.secretkey=b''

	def refresh(self):
		self.stdscr.erase()

		if self.height<4:
			self.stdscr.addstr(0,0,"WINDOW SIZE TOO SMALL!",color(curses.COLOR_WHITE,curses.COLOR_RED)|curses.A_BOLD)
		elif self.in_edit_mode:
			self.display.resize(self.height-min(self.editor.height,self.editor.pad.getmaxyx()[0])-2,-1)
			self.display.update()
			self.editor.update()
		else:
			self.display.resize(self.height-1,-1)
			self.display.update()
	
		self.stdscr.refresh()

	def keyEventLoop(self):
		while self.running:
			key=self.stdscr.get_wch()

			if key=='q':
				self.running=False
				break

			if key==curses.KEY_RESIZE:
				self.height,self.width=self.stdscr.getmaxyx()
				if self.height>=4:
					self.editor.resize(self.height//2,self.width)
					self.editor.move(self.height,0)
					self.display.resize(self.height-1,self.width-2)
					self.display.move(1,1)
				self.refresh()

			elif key==curses.KEY_MOUSE or not self.in_edit_mode:
				self.display.sendKey(key)
				self.refresh()

			elif self.in_edit_mode:
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

			elif key in (':','/'):
				self.in_edit_mode=True
				self.editor.initEditor(key)
				self.refresh()
				curses.curs_set(1)

	@abc.abstractmethod
	def start(self):...

	@abc.abstractmethod
	def sendMessage(self,msg:str):...

	@abc.abstractmethod
	def sendCommand(self,cmd:str):...

class ServerConsole(BaseConsole):
	def __init__(self,stdscr:curses.window,args):
		super().__init__(stdscr,args)

		self.clients:dict[str,socket.socket]={}
		self.clients_lock=threading.Lock()
		self.display_lock=threading.Lock()

	def broadcast(self,msg_type:int,msg_sender:str,msg:str,exclude:None|socket.socket=None):
		data=msg_type.to_bytes(1)+(msg_sender+'\0'+msg).encode()
		with self.clients_lock:
			for s in self.clients.values():
				if s==exclude:
					continue
				sendSocket(s,data)
		
		with self.display_lock:
			self.display.pushText(messageHeader(msg_type,msg_sender))
			self.display.pushText([msg,'\n'])

	def handleClient(self,client_socket:socket.socket,client_address):
		username=''
		try:
			if len(self.clients)+1==self.args.capacity:
				sendSocket(client_socket,"access denied: out of room capacity".encode())
				return
			sendSocket(client_socket,"access granted (0)".encode())

			client_key=readSocket(client_socket)
			if client_key!=self.secretkey:
				sendSocket(client_socket,"access denied: incorrect password".encode())
				return
			sendSocket(client_socket,"access granted (1)".encode())
	
			username=readSocket(client_socket).decode()
			with self.clients_lock:
				if username in self.clients:
					sendSocket(client_socket,"access denied: duplicated username".encode())
					return
				self.clients[username]=client_socket
			sendSocket(client_socket,"access granted (2)".encode())

			while True:
				readable,_,_=select.select([client_socket],[],[])
				if readable:
					msg=readSocket(client_socket).decode()
					if not msg:
						break
					self.broadcast(MSG_USER,username,msg)

				time.sleep(0.05)
		except:
			return
		finally:
			if username and username in self.clients:
				with self.clients_lock:
					self.clients.pop(username)
				self.broadcast(MSG_SYSTEM,"System",f"{username} has left the room.")

			client_socket.close()
			sendSocket(client_socket,MSG_EXIT.to_bytes(1))

	def start(self):
		try:
			raw_password=getpass.getpass("Please set the password (or leave it empty): ")
			self.secretkey=hashlib.sha256(raw_password.encode()).digest()

			server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
			server.bind(self.args.port)
			self.args.port=server.getsockname()[1]

			with self.display_lock:
				self.display.pushText(messageHeader(MSG_SYSTEM,"System"))
				self.display.pushText([f"Room {self.args.name} has opened on port {self.args.port}."])
				self.display.pushText([])

			self.stdscr.refresh()
			key_event_loop=threading.Thread(target=self.keyEventLoop)
			key_event_loop.start()

			server.listen(5)
			while self.running:
				client_socket,client_address=server.accept()
				thread=threading.Thread(target=self.handleClient,args=(client_socket,client_address))
				thread.start()

		except Exception as e:
			curses.endwin()
			print(f"error: {e.args[0]}")
		finally:
			self.running=False


	def sendMessage(self,msg:str):
		self.broadcast(MSG_ADMIN,self.args.username,msg)
		with self.display_lock:
			self.display.scrollDown(2**30)

	def sendCommand(self,cmd:str):
		pass

class ClientConsole(BaseConsole):
	def __init__(self,stdscr:curses._CursesWindow,args):
		super().__init__(stdscr,args)

		self.client_socket:socket.socket=socket.socket()

		self.display_lock=threading.Lock()

	def start(self):
		try:
			raw_password=getpass.getpass("Please enter the password (or leave it empty): ")
			self.secretkey=hashlib.sha256(raw_password.encode()).digest()

			client_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
			client_socket.connect(self.args.address)
			self.client_socket=client_socket

			res=readSocket(client_socket).decode()
			if res!="access granted (0)":
				raise Exception(res)

			sendSocket(client_socket,self.secretkey)
			res=readSocket(client_socket).decode()
			if res!="access granted (1)":
				raise Exception(res)

			sendSocket(client_socket,self.args.username.encode())
			res=readSocket(client_socket).decode()
			if res!="access granted (2)":
				raise Exception(res)

			self.stdscr.refresh()
			key_event_loop=threading.Thread(target=self.keyEventLoop)
			key_event_loop.start()

			while self.running:
				readable,_,_=select.select([client_socket],[],[])
				if readable:
					data=readSocket(client_socket)
					if data[0]==MSG_EXIT:
						break
					else:
						msg_sender,msg=data[1:].decode().split('\0')
						with self.display_lock:
							self.display.pushText(messageHeader(data[0],msg_sender))
							self.display.pushText([msg,'\n'])

				time.sleep(0.05)

		except Exception as e:
			curses.endwin()
			print(f"error: {e.args[0]}")
		finally:
			self.running=False
	
	def sendMessage(self,msg:str):
		with self.display_lock:
			self.display.pushText(messageHeader(MSG_USER,self.args.username))
			self.display.pushText([msg,'\n'])

		sendSocket(self.client_socket,msg.encode())

	def sendCommand(self,cmd:str):
		pass