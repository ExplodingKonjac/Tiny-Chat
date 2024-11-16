import argparse
from typing import Any

__args=None

def __parseAddress(value:str)->tuple[str,int]:
	try:
		host,port=value.split(":")
		return host,int(port)
	except ValueError:
		raise argparse.ArgumentTypeError("address should be in the form of 'host:port', such as '127.0.0.1:8080'")

def __parseCapacity(value:str)->int:
	try:
		ret=int(value)
		if ret<1:
			raise ValueError
		return ret
	except ValueError:
		raise argparse.ArgumentTypeError("capacity should be an integer larger than 1")

def __parseUsername(value:str)->str:
	if value.isprintable() and not ' ' in value:
		return value
	raise argparse.ArgumentTypeError("username cannot contain spaces or other invisible characters")

def parseArgs():
	global __args

	parser=argparse.ArgumentParser()
	subparsers=parser.add_subparsers(dest='command',help="subcommands",required=True)

	create_parser=subparsers.add_parser("create",help="create a chat room")
	create_parser.add_argument("username",type=__parseUsername,help="the username you want to use")
	create_parser.add_argument("-p","--port",type=int,default=0,help="the port which chat room will open on, automatically chosen if not specified")
	create_parser.add_argument("-t","--title",type=str,default="New Room",help="the title of the chat room")
	create_parser.add_argument("-c","--capacity",type=__parseCapacity,default=10,help="the maximum number of users in the room, 10 if not specified")

	join_parser=subparsers.add_parser("join",help="join a existing chat room")
	join_parser.add_argument("address",type=__parseAddress,help="the address of the room, in the form of 'host:port'")
	join_parser.add_argument("username",type=__parseUsername,help="the username you want to use")

	__args=parser.parse_args()

def args()->Any:
	return __args