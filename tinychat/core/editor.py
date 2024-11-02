from .basic import *

class Editor:
	def __init__(self,stdscr:curses.window,pos_y:int,pos_x:int,height:int,width:int):
		self.stdscr:curses.window=stdscr
		self.pos_y=pos_y
		self.pos_x=pos_x
		self.height=height
		self.width=width
		self.prompt=''
		self.buffer:list[str]=[]
		self.cursor_pos=0
		self.cursor_y=0
		self.cursor_x=0
		self.pad:curses.window=curses.newpad(1,1)
		self.begin_row=0
	
	def initEditor(self,prompt: str):
		self.buffer=[prompt]
		self.cursor_pos=1
		self.cursor_y=0
		self.cursor_x=1
		self.prompt=prompt

		self.updatePad()
	
	def sendKey(self,key:int|str)->str|None:
		if isinstance(key,str):
			if key=='\n' or key=='\r':
				return ''.join(self.buffer[1:])

			elif key.isprintable():
				self.buffer.insert(self.cursor_pos,key)
				self.cursor_pos+=1
				self.updatePad()
	
		elif isinstance(key,int):
			if key==curses.KEY_BACKSPACE or key==127:
				if self.cursor_pos>1:
					self.cursor_pos-=1
					self.buffer.pop(self.cursor_pos)
					self.updatePad()
				elif len(self.buffer)==1:
					return ''
	
			elif key==curses.KEY_DC:
				if self.cursor_pos<len(self.buffer):
					self.buffer.pop(self.cursor_pos)
					self.updatePad()
	
			elif key==curses.KEY_LEFT:
				if self.cursor_pos>1:
					self.cursor_pos-=1
	
			elif key==curses.KEY_RIGHT:
				if self.cursor_pos<len(self.buffer):
					self.cursor_pos+=1

			elif key==curses.KEY_HOME:
				self.cursor_pos=1

			elif key==curses.KEY_END:
				self.cursor_pos=len(self.buffer)

		return None
	
	def updatePad(self):
		self.pad=drawText(self.buffer,self.width)

	def resize(self,height:int,width:int):
		new_height=0
		if height!=-1 and height!=self.height:
			self.height=height

		if width!=-1 and width!=self.width:
			self.width=width
			old_height=self.pad.getmaxyx()[0]
			self.updatePad()
			new_height=self.pad.getmaxyx()[0]
			self.begin_row=round(self.begin_row*new_height/old_height)

		self.begin_row=max(min(self.begin_row,new_height-self.height),0)

	def move(self,pos_y:int,pos_x:int):
		self.pos_y=pos_y
		self.pos_x=pos_x

	def update(self):
		actual_height=self.pad.getmaxyx()[0]
		self.cursor_y,self.cursor_x=getCursorPos(self.buffer,self.cursor_pos,self.width)
		scr_row=0

		if actual_height<=self.height:
			scr_row=self.pos_y-actual_height
			self.begin_row=0
		else:
			if self.begin_row>self.cursor_y:
				self.begin_row=self.cursor_y
			elif self.begin_row+self.height-1<self.cursor_y:
				self.begin_row=self.cursor_y-self.height+1

			scr_row=self.pos_y-self.height
			actual_height=self.height

		self.pad.overwrite(self.stdscr,self.begin_row,0,scr_row,self.pos_x,scr_row+actual_height-1,self.pos_x+self.width-1)
		self.stdscr.hline(scr_row-1,self.pos_x,curses.ACS_HLINE,self.width)
		self.stdscr.move(scr_row+self.cursor_y-self.begin_row,self.pos_x+self.cursor_x)