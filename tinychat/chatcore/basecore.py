import abc
import socket
import select
import threading
from typing import Callable

from ..basic.network import *
from ..basic.settings import *

MSG_SYSTEM=1
MSG_USER=2
MSG_ADMIN=3
MSG_SELF=4
CMD_EXIT=5
CMD_GRANTED=6
QRY_USERLIST=7

class BaseCore(abc.ABC):
	def __init__(self,on_new_message:Callable[[int,str,str],None]):
		self._onNewMessage=on_new_message

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
