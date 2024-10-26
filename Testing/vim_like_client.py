import curses

def get_command(stdscr, prompt=":"):
    """获取用户输入，并支持左右箭头移动光标、自动换行"""
    curses.echo(False)  # 关闭自动回显
    stdscr.addstr(prompt)  # 显示提示符
    stdscr.refresh()

    command = []  # 用来保存输入的字符
    cursor_pos = 0  # 当前光标在命令中的位置

    # 获取屏幕的高度和宽度
    height, width = stdscr.getmaxyx()

    while True:
        key = stdscr.get_wch()

        if isinstance(key,str) and key == '\n':  # 回车键 (Enter)
            break

        elif key == curses.KEY_BACKSPACE or key == 127:  # 处理退格键
            if cursor_pos > 0:
                cursor_pos -= 1
                command.pop(cursor_pos)  # 删除光标前的字符
                refresh_command(stdscr, command, cursor_pos, prompt, height, width)

        elif key == curses.KEY_LEFT:  # 左箭头移动光标
            if cursor_pos > 0:
                cursor_pos -= 1
                refresh_command(stdscr, command, cursor_pos, prompt, height, width)

        elif key == curses.KEY_RIGHT:  # 右箭头移动光标
            if cursor_pos < len(command):
                cursor_pos += 1
                refresh_command(stdscr, command, cursor_pos, prompt, height, width)
        
        elif key == curses.KEY_HOME:  # Home 键
            cursor_pos = 0
            refresh_command(stdscr, command, cursor_pos, prompt, height, width)

        elif key == curses.KEY_END:  # End 键
            cursor_pos = len(command)
            refresh_command(stdscr, command, cursor_pos, prompt, height, width)

        else:  # 处理其他字符输入
            command.insert(cursor_pos, key)
            cursor_pos += 1
            refresh_command(stdscr, command, cursor_pos, prompt, height, width)

    return ''.join(command)

def refresh_command(stdscr, command, cursor_pos, prompt, height, width):
    """刷新显示的命令，并重新定位光标"""

    # 逐行显示命令内容
    line_cnt = (len(prompt) + len(command) + width) // width
    for i in range(line_cnt):
        stdscr.move(height - i - 1, 0)
        stdscr.clrtoeol()
    stdscr.addstr(height - line_cnt, 0, prompt + ''.join(command))

    # 根据光标在命令中的位置定位光标
    cursor_line = height - line_cnt + (len(prompt) + cursor_pos) // width
    cursor_col = (len(prompt) + cursor_pos) % width
    stdscr.move(cursor_line, cursor_col)
    stdscr.refresh()

def main(stdscr):
    curses.curs_set(0)  # 隐藏光标
    stdscr.clear()

    height, width = stdscr.getmaxyx()
    command_history = []
    history_offset = 0

    stdscr.addstr(0, 0, "按 `:` 键进入命令模式，按上下箭头滚动历史，按 `q` 退出")

    while True:
        key = stdscr.getch()

        if key == ord(':'):
            # 进入命令模式
            curses.curs_set(1)  # 显示光标
            stdscr.move(height - 1, 0)
            stdscr.clrtoeol()  # 清除行内容
            command = get_command(stdscr, ":")  # 获取不限制长度的命令

            # 将命令保存到历史中
            command_history.append(command)
            history_offset = 0

            # 恢复主界面
            curses.curs_set(0)  # 隐藏光标
            stdscr.addstr(height - 1, 0, " " * (width - 1))  # 清空底部行

        elif key == ord('q'):
            break

        elif key == curses.KEY_UP:
            if history_offset < len(command_history) - 1:
                history_offset += 1

        elif key == curses.KEY_DOWN:
            if history_offset > 0:
                history_offset -= 1

        # 清除上半部分内容
        stdscr.move(1, 0)
        stdscr.clrtobot()

        # 显示命令历史
        for i, cmd in enumerate(command_history[-(height - 2 + history_offset):len(command_history) - history_offset]):
            stdscr.addstr(i + 1, 0, f"你输入的命令是: {cmd}")

        stdscr.refresh()

if __name__ == "__main__":
    curses.wrapper(main)
