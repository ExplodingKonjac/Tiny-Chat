from typing import Callable
from .basecore import *

class UserData:
	def __init__(self,name:str,s:socket.socket):
		self.name=name
		self.socket=s
		self.lock=threading.Lock()
		self.kicked=False

class ServerCore(BaseCore):
	def __init__(self,**kwargs):
		super().__init__(**kwargs)

		self._clients:dict[str,UserData]={}
		self._clients_lock=threading.Lock()

	def _broadcastMessage(self,msg_type:int,msg_sender:str,msg:str,exclude:None|str=None):
		self._broadcastData(msg_type.to_bytes(1)+(msg_sender+'\0'+msg).encode(),exclude)
		self._onNewMessage(MSG_SELF if msg_type==MSG_ADMIN else msg_type,msg_sender,msg)
	
	def _broadcastData(self,data:bytes,exclude:None|str=None):
		with self._clients_lock:
			for user in self._clients.values():
				if user.name!=exclude:
					sendSocket(user.socket,data)

	def _handleClient(self,client_socket:socket.socket,client_address:tuple[str,int]):
		joined=False
		user=UserData('',client_socket)
		try:
			if len(self._clients)+1==args().capacity:
				sendSocket(client_socket,"access denied: out of room capacity".encode())
				return
			sendSocket(client_socket,CMD_GRANTED.to_bytes(1))

			client_key=readSocket(client_socket)
			if client_key!=args().secretkey:
				sendSocket(client_socket,"access denied: incorrect password".encode())
				return
			sendSocket(client_socket,CMD_GRANTED.to_bytes(1))

			user.name=readSocket(client_socket).decode()
			with self._clients_lock:
				if user.name in self._clients or user.name==args().username:
					sendSocket(client_socket,"access denied: duplicated username".encode())
					return
				self._clients[user.name]=user
			sendSocket(client_socket,CMD_GRANTED.to_bytes(1)+args().title.encode())

			joined=True
			self._broadcastData(MSG_NEWUSER.to_bytes(1)+'\0'.join([user.name,client_address[0],str(client_address[1])]).encode(),user.name)
			self._onNewUser(client_address,user.name)

			while self._running:
				readable,_,_=select.select([client_socket],[],[],0.1)
				if not readable:
					continue

				with user.lock:
					msg=readSocket(client_socket)
					if not msg:
						break

					elif msg[0]==MSG_USER:
						self._broadcastMessage(MSG_USER,user.name,msg[1:].decode(),user.name)

					elif msg[0]==QRY_USERLIST:
						sendSocket(client_socket,'\0'.join(self.queryUserList()).encode())

		except:
			sendSocket(client_socket,CMD_EXIT.to_bytes(1))

		finally:
			if joined:
				with self._clients_lock:
					self._clients.pop(user.name)
				self._broadcastData(MSG_USERLEFT.to_bytes(1)+user.kicked.to_bytes(1)+user.name.encode(),user.name)
			client_socket.close()

			self._onUserLeft(user.name,user.kicked)

	def _serverLoop(self,server_socket:socket.socket):
		threads=[]
		try:
			server_socket.listen(5)
			while self._running:
				readable,_,_=select.select([server_socket],[],[],0.1)
				if not readable:
					continue

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
			server_socket.bind(('0.0.0.0',args().port))
			if args().port==0:
				args().port=server_socket.getsockname()[1]

			self._onJoinRoom(('localhost',args().port),args().title)

			self._main_thread=threading.Thread(target=self._serverLoop,args=(server_socket,))
			self._main_thread.start()

		except Exception as e:
			self._error_msg=', '.join(map(str,e.args))
			self._running=False

	def sendMessage(self,msg:str):
		self._broadcastMessage(MSG_ADMIN,args().username,msg)
	
	def queryUserList(self)->list[str]:
		return (list(self._clients.keys())+[args().username])

	def kick(self,username:str):
		if not username in self._clients:
			raise Exception(f"no kickable user named '{username}'")

		with self._clients_lock:
			user=self._clients[username]
			with user.lock:
				sendSocket(user.socket,CMD_EXIT.to_bytes(1))
				user.kicked=True
