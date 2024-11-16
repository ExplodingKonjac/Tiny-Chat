import abc
import socket
import select
import threading
import enum
from typing import Callable

from ..basic.settings import *
from ..basic.network import *

MSG_SYSTEM=1
MSG_USER=2
MSG_ADMIN=3
MSG_SELF=4
MSG_NEWUSER=5
MSG_USERLEFT=6

CMD_EXIT=101
CMD_GRANTED=102

QRY_USERLIST=201

class BaseCore(abc.ABC):
	def __init__(self,*,
				 on_new_message:Callable[[int,str,str],None],
				 on_join_room:Callable[[tuple[str,int],str],None],
				 on_left_room:Callable[[],None],
				 on_new_user:Callable[[tuple[str,int],str],None],
				 on_user_left:Callable[[str,bool],None]):
		self._onNewMessage=on_new_message
		self._onJoinRoom=on_join_room
		self._onLeftRoom=on_left_room
		self._onNewUser=on_new_user
		self._onUserLeft=on_user_left

		self._running=False
		self._error_msg=''
		self._main_thread=threading.Thread()

	@abc.abstractmethod
	def start(self)->str|None:...

	def terminate(self)->None:
		self._running=False
		self._main_thread.join()

	@abc.abstractmethod
	def sendMessage(self,msg:str):...

	@abc.abstractmethod
	def queryUserList(self)->list[str]:...

	@property
	def error_msg(self):
		return self._error_msg
	
	@property
	def running(self):
		return self._running