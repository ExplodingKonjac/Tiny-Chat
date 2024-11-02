## 安装

将项目 clone 下来，进入项目根目录，运行命令：

```
pip install .
```

或者这样设置安装路径：

```
pip install --prefix="/your/custom/path/" .
```

执行完命令后，可执行文件 `tinychat` 会被安装在 `install_prefix/local/bin/` 下，其中 `install_prefix` 是默认安装路径或通过 `--prefix` 设置的路径。你可能需要根据安装路径设置 PATH 环境变量。


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

进入 chat 界面之后，键入 `:` 后可以输入消息，键入 `/` 后可以输入命令。

### 命令

* `/quit`：退出程序。