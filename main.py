import curses
import argparse

import core

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

def parseArgs():
	parser=argparse.ArgumentParser()
	subparsers=parser.add_subparsers(dest='command',help="subcommands")

	create_parser=subparsers.add_parser("create",help="create a chat room")
	create_parser.add_argument("username",type=str,help="the username you want to use")
	create_parser.add_argument("-p","--port",type=int,default=0,help="the port which chat room will open on, automatically chosen if not specified")
	create_parser.add_argument("-n","--name",type=str,default="New Room",help="the name of the chat room")
	create_parser.add_argument("-c","--capacity",type=parseCapacity,help="the maximum number of users in the room")

	join_parser=subparsers.add_parser("join",help="join a existing chat room")
	join_parser.add_argument("address",type=parseAddress,help="the address of the room, in the form of 'host:port'")
	join_parser.add_argument("username",type=str,help="the username you want to use")

	return parser.parse_args()

def main(stdscr:curses.window,args):
	curses.mousemask(curses.ALL_MOUSE_EVENTS)
	curses.curs_set(0)
	curses.echo(False)
	curses.start_color()
	curses.endwin()

	stdscr.keypad(True)

	if args.command=="create":
		con=core.ServerConsole(stdscr,args)
	else:
		con=core.ClientConsole(stdscr,args)
	con.start()

if __name__=="__main__":
	args=parseArgs()
	curses.wrapper(main,args)
