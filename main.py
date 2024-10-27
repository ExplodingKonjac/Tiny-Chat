import curses
import argparse

import core

def parseAddress(value:str):
	try:
		host,port=value.split(":")
		port=int(port)
		return host,port
	except ValueError:
		raise argparse.ArgumentTypeError("address should be in the form of 'host:port', such as '127.0.0.1:8080'")

def parseArgs():
	parser=argparse.ArgumentParser()
	subparsers=parser.add_subparsers(dest='command',help="subcommands")

	create_parser=subparsers.add_parser("create",help="create a chat room")
	create_parser.add_argument("username",type=str,help="the username you want to use")
	create_parser.add_argument("-p","--port",type=int,default=0,help="the port which chat room will open on, automatically chosen if not specified")
	create_parser.add_argument("-n","--name",type=str,default="New Room",help="the name of the chat room")
	create_parser.add_argument("--password",type=str,default="",help="the password needed to enter the room, empty if not specified")

	join_parser=subparsers.add_parser("join",help="join a existing chat room")
	join_parser.add_argument("address",type=parseAddress,help="the address of the room, in the form of 'host:port'")
	join_parser.add_argument("username",type=str,help="the username you want to use")

	return parser.parse_args()

def main(stdscr:curses.window):
	curses.mousemask(curses.ALL_MOUSE_EVENTS)
	curses.curs_set(0)
	curses.echo(False)
	curses.start_color()

	stdscr.keypad(True)
	stdscr.refresh()

	height,width=stdscr.getmaxyx()
	con=core.Console(stdscr,height,width)

	for i in range(1,30):
		con.display.pushText([
			core.colorAttr(curses.COLOR_BLUE,curses.COLOR_BLACK),
			"This is line ",
			core.colorAttr(curses.COLOR_RED,curses.COLOR_BLACK),
			str(i),
			0,
			" blah"*i
		])
	con.refresh()

	con.keyEventLoop()

if __name__=="__main__":
	# parseArgs()
	curses.wrapper(main)
