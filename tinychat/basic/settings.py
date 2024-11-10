import argparse

args=None

def parseAddress(value:str)->tuple[str,int]:
	try:
		host,port=value.split(":")
		return host,int(port)
	except ValueError:
		raise argparse.ArgumentTypeError("address should be in the form of 'host:port', such as '127.0.0.1:8080'")

def parseCapacity(value:str)->int:
	try:
		ret=int(value)
		if ret<1:
			raise ValueError
		return ret
	except ValueError:
		raise argparse.ArgumentTypeError("capacity should be an integer larger than 1")

def parseUsername(value:str)->str:
	if value.isprintable() and not ' ' in value:
		return value
	raise argparse.ArgumentTypeError("username cannot contain spaces or other invisible characters")

def parseArgs():
	global args

	parser=argparse.ArgumentParser()
	subparsers=parser.add_subparsers(dest='command',help="subcommands",required=True)

	create_parser=subparsers.add_parser("create",help="create a chat room")
	create_parser.add_argument("username",type=parseUsername,help="the username you want to use")
	create_parser.add_argument("-p","--port",type=int,default=0,help="the port which chat room will open on, automatically chosen if not specified")
	create_parser.add_argument("-n","--name",type=str,default="New Room",help="the name of the chat room")
	create_parser.add_argument("-c","--capacity",type=parseCapacity,default=10,help="the maximum number of users in the room, 10 if not specified")

	join_parser=subparsers.add_parser("join",help="join a existing chat room")
	join_parser.add_argument("address",type=parseAddress,help="the address of the room, in the form of 'host:port'")
	join_parser.add_argument("username",type=parseUsername,help="the username you want to use")

	args=parser.parse_args()
