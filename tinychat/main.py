import curses
import hashlib
import signal
import getpass

from .basic.settings import *
from .chatcore import *
from .gui import *

def cursesMain(stdscr:curses.window,args):
	curses.mousemask(curses.ALL_MOUSE_EVENTS)
	curses.curs_set(0)
	curses.echo(False)
	curses.start_color()

	if args.command=="create":
		win=MainWindow(stdscr,ServerCore)
	else:
		win=MainWindow(stdscr,ClientCore)

	stdscr.refresh()
	return win.main()

def main():
	signal.signal(signal.SIGINT,signal.SIG_IGN)

	parseArgs()

	prompt=f"Please {'set' if args().command=='create' else 'enter'} the password (or leave it empty): "
	args().secretkey=hashlib.sha256(getpass.getpass(prompt).encode()).digest()

	error_msg=curses.wrapper(cursesMain,args())
	if error_msg:
		print(f"error: {error_msg}")

if __name__=="__main__":
	main()