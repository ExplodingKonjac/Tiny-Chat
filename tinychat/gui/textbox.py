from ..basic.graphics import *

class Textbox:
	def __init__(self,stdscr:curses.window,pos_y:int,pos_x:int,height:int,width:int):
		self._stdscr=stdscr
		self._pos_y=pos_y
		self._pos_x=pos_x
		self._height=height
		self._width=width
		self._texts:list[list[str|int]]=[]
		self._pad=curses.window=curses.newpad(1,width)
		self._begin_row=0
		self._actual_height=0
		self._new_text=False

	def scrollUp(self,dt:int):
		if self._actual_height>=self._height:
			self._begin_row=max(self._begin_row-dt,0)

	def scrollDown(self,dt:int):
		if self._actual_height>=self._height:
			self._begin_row=min(self._begin_row+dt,self._actual_height-self._height)
			if self._begin_row==self._actual_height-self._height:
				self._new_text=False

	def sendKey(self,key:int|str):
		if isinstance(key,int):
			if key==curses.KEY_MOUSE:
				_,x,y,_,bstate=curses.getmouse()
				if bstate&curses.BUTTON4_PRESSED: # scroll up
					self.scrollUp(3)
				elif bstate&curses.BUTTON5_PRESSED: # scroll down
					self.scrollDown(3)

			elif key==curses.KEY_UP:
				self.scrollUp(1)

			elif key==curses.KEY_DOWN:
				self.scrollDown(1)

			elif key==curses.KEY_PPAGE:
				self.scrollUp(self._height)

			elif key==curses.KEY_NPAGE:
				self.scrollDown(self._height)
			
			elif key==curses.KEY_HOME:
				self.scrollUp(10**9)
			
			elif key==curses.KEY_END:
				self.scrollDown(10**9)

	def pushText(self,text:list[str|int]):
		self._texts.append(text)

		new_pad=drawText(text,self._width)
		dt_height=new_pad.getmaxyx()[0]

		tmp=self._pad.getmaxyx()[0]
		while self._actual_height+dt_height>tmp:
			tmp*=2
		self._pad.resize(tmp,self._width)
		new_pad.overwrite(self._pad,0,0,self._actual_height,0,self._actual_height+dt_height-1,self._width-1)

		is_latest=(self._actual_height<self._height or self._begin_row+self._height==self._actual_height)
		self._actual_height+=dt_height
		if is_latest:
			self._begin_row=max(0,self._actual_height-self._height)
		else:
			self._new_text=True

	def move(self,_pos_y:int,_pos_x:int):
		self._pos_y=_pos_y
		self._pos_x=_pos_x

	def resize(self,_height:int,_width:int):
		if _height!=-1 and _height!=self._height:
			self._begin_row=max(min(self._begin_row-(_height-self._height),self._actual_height-_height),0)
			self._height=_height

		if _width!=-1 and _width!=self._width:
			self._pad.resize(1,_width)

			_actual_height=0
			for text in self._texts:
				new_pad=drawText(text,_width)
				dt_height=new_pad.getmaxyx()[0]

				tmp=self._pad.getmaxyx()[0]
				while _actual_height+dt_height>tmp:
					tmp*=2
				self._pad.resize(tmp,_width)

				new_pad.overwrite(self._pad,0,0,_actual_height,0,_actual_height+dt_height-1,_width-1)
				_actual_height+=dt_height

			self._begin_row=round(self._begin_row*_actual_height/self._actual_height)
			self._width=_width
			self._actual_height=_actual_height

	def update(self):
		_height=max(1,min(self._height,self._actual_height))
		self._pad.overwrite(self._stdscr,self._begin_row,0,self._pos_y,self._pos_x,self._pos_y+_height-1,self._pos_x+self._width-1)

	def hasNewText(self)->bool:
		return self._new_text