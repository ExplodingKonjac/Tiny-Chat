## 安装

将项目 clone 下来，进入项目根目录，运行命令：

```
pip install .
```

也可以通过设置 pip 选项来更改安装位置。该命令会安装可执行文件 `tinychat`，可能需要根据可执行文件的安装路径设置 PATH。


注意：在 Windows 下，需要先安装 `windows-curses` 包：

```
pip install windows-curses
```

## 使用

用下面命令查看帮助：

```
tinychat --help
```

对于具体的 `subcommand`，这样查看帮助：

```
tinychat subcommand --help
```

进入 chat 界面之后，键入 `:` 后可以输入消息，键入 `/` 后可以输入命令（注意要在英文输入状态键入）。

### 命令

* `/quit`：退出程序。