import curses

def main(stdscr):
    stdscr.addstr(0, 0, f"Press or 'q' to quit.")
    stdscr.refresh()

    while True:
        key = stdscr.get_wch()

        if key == 'q':
            break
        elif key == curses.KEY_HOME:
            stdscr.addstr(1, 0, "bingo!")
            stdscr.clrtoeol()
        else:
            stdscr.addstr(1, 0, f"key {key} pressed!")
            stdscr.clrtoeol()
        stdscr.refresh()

curses.wrapper(main)
