from typing import Callable
from .basecore import *

class ServerCore(BaseCore):
	def __init__(self,
				 on_new_message:Callable[[int, str, str],None],
				 on_new_user:Callable[[str,socket.socket],None],
				 on_user_left:Callable[[str],None]):
		super().__init__(on_new_message)

		self._onNewUser=on_new_user
		self._onUserLeft=on_user_left

		self._clients:dict[str,socket.socket]={}
		self._clients_lock=threading.Lock()

	def _broadcast(self,msg_type:int,msg_sender:str,msg:str,exclude:None|socket.socket=None):
		data=msg_type.to_bytes(1)+(msg_sender+'\0'+msg).encode()
		with self._clients_lock:
			for s in self._clients.values():
				if s==exclude:
					continue
				sendSocket(s,data)

		if msg_type==MSG_ADMIN:
			msg_type=MSG_USER
		self._onNewMessage(msg_type,msg_sender,msg)

	def _handleClient(self,client_socket:socket.socket,client_address):
		username=''
		joined=False
		try:
			if len(self._clients)+1==args.capacity:
				sendSocket(client_socket,"access denied: out of room capacity".encode())
				return
			sendSocket(client_socket,CMD_GRANTED.to_bytes(1))

			client_key=readSocket(client_socket)
			if client_key!=args.secretkey:
				sendSocket(client_socket,"access denied: incorrect password".encode())
				return
			sendSocket(client_socket,CMD_GRANTED.to_bytes(1))

			username=readSocket(client_socket).decode()
			with self._clients_lock:
				if username in self._clients or username==args.username:
					sendSocket(client_socket,"access denied: duplicated username".encode())
					return
				self._clients[username]=client_socket
			sendSocket(client_socket,CMD_GRANTED.to_bytes(1)+args.name.encode())

			joined=True
			self._broadcast(MSG_SYSTEM,"System",f"{username} has joined the room.",client_socket)
			self._onNewUser(username,client_socket)

			while self._running:
				readable,_,_=select.select([client_socket],[],[],0.1)
				if readable:
					msg=readSocket(client_socket).decode()
					if not msg:
						break
					elif msg[0]==MSG_USER:
						self._broadcast(MSG_USER,username,msg[1:],client_socket)
					elif msg[0]==QRY_USERLIST:
						sendSocket(client_socket,'\0'.join(self.queryUserList()).encode())

		except:
			sendSocket(client_socket,CMD_EXIT.to_bytes(1))
		finally:
			if joined:
				with self._clients_lock:
					self._clients.pop(username)
				self._broadcast(MSG_SYSTEM,"System",f"{username} has left the room.",client_socket)
			client_socket.close()

			self._onUserLeft(username)

	def _serverLoop(self,server_socket:socket.socket):
		threads=[]
		try:
			server_socket.listen(5)
			while self._running:
				readable,_,_=select.select([server_socket],[],[],0.1)
				if readable:
					client_socket,client_address=server_socket.accept()
					thread=threading.Thread(target=self._handleClient,args=(client_socket,client_address))
					thread.start()
					threads.append(thread)

		except Exception as e:
			self._error_msg=', '.join(map(str,e.args))
			self._running=False
		finally:
			for thread in threads:
				thread.join()
			server_socket.close()

	def start(self):
		try:
			self._running=True

			server_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
			server_socket.bind(('0.0.0.0',args.port))
			if args.port==0:
				args.port=server_socket.getsockname()[1]

			self._onNewMessage(MSG_SYSTEM,"System","Room '{self.args.name}' has opened on port {self.args.port}.")

			self._main_thread=threading.Thread(target=self._serverLoop,args=(server_socket,))
			self._main_thread.start()

		except Exception as e:
			self._error_msg=', '.join(map(str,e.args))
			self._running=False

	def sendMessage(self,msg:str):
		self._broadcast(MSG_ADMIN,args.username,msg)
	
	def queryUserList(self)->list[str]:
		return list(self._clients.keys())
