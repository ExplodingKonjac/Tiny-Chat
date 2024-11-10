from typing import Callable
from .basecore import *

class ClientCore(BaseCore):
	def __init__(self,
			  	 on_new_message:Callable[[int, str, str],None]):		
		super().__init__(on_new_message)

		self._client_socket:socket.socket=socket.socket()
		self._send_lock=threading.Lock()
		self._read_lock=threading.Lock()

	def clientLoop(self):
		try:
			while self._running:
				readable,_,_=select.select([self._client_socket],[],[],0.1)
				if readable:
					with self._read_lock:
						data=readSocket(self._client_socket)
					if not data:
						raise Exception("room closed or unable to connect to host")
					elif data[0]==CMD_EXIT:
						raise Exception("connection closed or being kicked by host")
					elif data[0]==MSG_USER or data[0]==MSG_ADMIN:
						msg_sender,msg=data[1:].decode().split('\0')
						self._onNewMessage(data[0],msg_sender,msg)

		except Exception as e:
			self._error_msg=', '.join(map(str,e.args))
			self._running=False
		finally:
			self._client_socket.close()
	
	def start(self):
		try:
			self._running=True

			self._client_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
			self._client_socket.connect(args.address)

			res=readSocket(self._client_socket)
			if not res or res[0]!=CMD_GRANTED:
				self._error_msg=res.decode()
				return

			sendSocket(self._client_socket,args.secretkey)
			res=readSocket(self._client_socket)
			if not res or res[0]!=CMD_GRANTED:
				self._error_msg=res.decode()
				return

			sendSocket(self._client_socket,args.username.encode())
			res=readSocket(self._client_socket)
			if not res or res[0]!=CMD_GRANTED:
				self._error_msg=res.decode()
				return
			args.name=res[1:].decode()
			
			self._onNewMessage(MSG_SYSTEM,"System",f"You have joined the room '{args.name}' at {args.address[0]}:{args.address[1]}\n")

			self._main_thread=threading.Thread(target=self.clientLoop)
			self._main_thread.start()

		except Exception as e:
			self._error_msg=', '.join(map(str,e.args))
			self._running=False
	
	def sendMessage(self,msg:str):
		with self._send_lock:
			sendSocket(self._client_socket,MSG_USER.to_bytes(1)+msg.encode())
		self._onNewMessage(MSG_SELF,args.username,msg)

	def queryUserList(self)->list[str]:
		with self._send_lock:
			sendSocket(self._client_socket,QRY_USERLIST.to_bytes(1))
		with self._read_lock:
			data=readSocket(self._client_socket)
		return data.decode().split('\0')
