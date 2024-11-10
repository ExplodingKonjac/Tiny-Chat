import curses
import argparse
import hashlib
import signal

from .basic.settings import *
from .chatcore import *
from .gui import *

def cursesMain(stdscr:curses.window,args):
	curses.mousemask(curses.ALL_MOUSE_EVENTS)
	curses.curs_set(0)
	curses.echo(False)
	curses.start_color()

	if args.command=="create":
		con=ServerConsole(stdscr,args)
	else:
		con=ClientConsole(stdscr,args)

	stdscr.refresh()
	con.start()
	return con.error_msg

def main():
	signal.signal(signal.SIGINT,signal.SIG_IGN)

	parseArgs()

	raw_password=input(f"Please {'set' if args.command=='create' else 'enter'} the password (or leave it empty): ")
	args.secretkey=hashlib.sha256(raw_password.encode()).digest()
	del raw_password

	error_msg=curses.wrapper(cursesMain,args)
	if error_msg:
		print(f"error: {error_msg}")

if __name__=="__main__":
	main()