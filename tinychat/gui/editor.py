from ..basic.graphics import *

class Editor:
	def __init__(self,stdscr:curses.window,pos_y:int,pos_x:int,height:int,width:int):
		self._stdscr:curses.window=stdscr
		self._pos_y=pos_y
		self._pos_x=pos_x
		self._height=height
		self._width=width
		self._prompt=''
		self._buffer:list[str]=[]
		self._cursor_pos=0
		self._pad:curses.window=curses.newpad(1,1)
		self._begin_row=0
	
	def initEditor(self,_prompt: str):
		self._buffer=[_prompt]
		self._cursor_pos=1
		self._prompt=_prompt

		self.updatePad()
	
	def sendKey(self,key:int|str)->str|None:
		if key==curses.KEY_BACKSPACE or key==127 or key=='\b':
			if self._cursor_pos>1:
				self._cursor_pos-=1
				self._buffer.pop(self._cursor_pos)
				self.updatePad()
			elif len(self._buffer)==1:
				return ''

		elif isinstance(key,str):
			if key=='\n' or key=='\r':
				return ''.join(self._buffer[1:])

			elif key.isprintable():
				self._buffer.insert(self._cursor_pos,key)
				self._cursor_pos+=1
				self.updatePad()
	
		elif key==curses.KEY_DC:
			if self._cursor_pos<len(self._buffer):
				self._buffer.pop(self._cursor_pos)
				self.updatePad()

		elif key==curses.KEY_LEFT:
			if self._cursor_pos>1:
				self._cursor_pos-=1

		elif key==curses.KEY_RIGHT:
			if self._cursor_pos<len(self._buffer):
				self._cursor_pos+=1

		elif key==curses.KEY_HOME:
			self._cursor_pos=1

		elif key==curses.KEY_END:
			self._cursor_pos=len(self._buffer)

		return None
	
	def updatePad(self):
		self._pad=drawText(self._buffer,self._width)

	def resize(self,_height:int,_width:int):
		new_height=0
		if _height!=-1 and _height!=self._height:
			self._height=_height

		if _width!=-1 and _width!=self._width:
			self._width=_width
			old_height=self._pad.getmaxyx()[0]
			self.updatePad()
			new_height=self._pad.getmaxyx()[0]
			self._begin_row=round(self._begin_row*new_height/old_height)

		self._begin_row=max(min(self._begin_row,new_height-self._height),0)

	def move(self,_pos_y:int,_pos_x:int):
		self._pos_y=_pos_y
		self._pos_x=_pos_x

	def update(self):
		actual_height=self._pad.getmaxyx()[0]
		_cursor_y,_cursor_x=getCursorPos(self._buffer,self._cursor_pos,self._width)
		scr_row=0

		if actual_height<=self._height:
			scr_row=self._pos_y-actual_height
			self._begin_row=0
		else:
			if self._begin_row>_cursor_y:
				self._begin_row=_cursor_y
			elif self._begin_row+self._height-1<_cursor_y:
				self._begin_row=_cursor_y-self._height+1

			scr_row=self._pos_y-self._height
			actual_height=self._height

		self._pad.overwrite(self._stdscr,self._begin_row,0,scr_row,self._pos_x,scr_row+actual_height-1,self._pos_x+self._width-1)
		self._stdscr.hline(scr_row-1,self._pos_x,curses.ACS_HLINE,self._width)
		self._stdscr.move(scr_row+_cursor_y-self._begin_row,self._pos_x+_cursor_x)
	
	@property
	def actual_height(self):
		return min(self._height,self._pad.getmaxyx()[0])