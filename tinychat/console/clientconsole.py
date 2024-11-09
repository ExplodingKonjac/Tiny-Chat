from .baseconsole import *

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
	
	def start(self):
		client_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		try:
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
			client_socket.close()
	
	def sendMessage(self,msg:str):
		with self.window_lock:
			self.display.pushText(messageHeader(MSG_SELF,self.args.username))
			self.display.pushText([msg,'\n'])
			self.refresh()

		sendSocket(self.client_socket,msg.encode())
