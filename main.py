import curses
import argparse

import core

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
			core.colorAttr(curses.COLOR_RED,curses.COLOR_BLACK)|curses.A_CHARTEXT,
			str(i),
			0,
			" blah"*i
		])
	con.refresh()

	con.keyEventLoop()

if __name__=="__main__":
	curses.wrapper(main)
