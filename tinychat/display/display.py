from ..basic.graphics import *

class Display:
	def __init__(self,stdscr:curses.window,pos_y:int,pos_x:int,height:int,width:int):
		self.stdscr=stdscr
		self.pos_y=pos_y
		self.pos_x=pos_x
		self.height=height
		self.width=width
		self.texts:list[list[str|int]]=[]
		self.pad=curses.window=curses.newpad(1,width)
		self.begin_row=0
		self.actual_height=0
		self.new_message=False

	def scrollUp(self,dt:int):
		if self.actual_height>=self.height:
			self.begin_row=max(self.begin_row-dt,0)

	def scrollDown(self,dt:int):
		if self.actual_height>=self.height:
			self.begin_row=min(self.begin_row+dt,self.actual_height-self.height)
			if self.begin_row==self.actual_height-self.height:
				self.new_message=False

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
				self.scrollUp(self.height)

			elif key==curses.KEY_NPAGE:
				self.scrollDown(self.height)
			
			elif key==curses.KEY_HOME:
				self.scrollUp(10**9)
			
			elif key==curses.KEY_END:
				self.scrollDown(10**9)

	def pushText(self,text:list[str|int]):
		self.texts.append(text)

		new_pad=drawText(text,self.width)
		dt_height=new_pad.getmaxyx()[0]

		tmp=self.pad.getmaxyx()[0]
		while self.actual_height+dt_height>tmp:
			tmp*=2
		self.pad.resize(tmp,self.width)
		new_pad.overwrite(self.pad,0,0,self.actual_height,0,self.actual_height+dt_height-1,self.width-1)

		is_latest=(self.actual_height<self.height or self.begin_row+self.height==self.actual_height)
		self.actual_height+=dt_height
		if is_latest:
			self.begin_row=max(0,self.actual_height-self.height)
		else:
			self.new_message=True

	def move(self,pos_y:int,pos_x:int):
		self.pos_y=pos_y
		self.pos_x=pos_x

	def resize(self,height:int,width:int):
		if height!=-1 and height!=self.height:
			self.begin_row=max(min(self.begin_row-(height-self.height),self.actual_height-height),0)
			self.height=height

		if width!=-1 and width!=self.width:
			self.pad.resize(1,width)

			actual_height=0
			for text in self.texts:
				new_pad=drawText(text,width)
				dt_height=new_pad.getmaxyx()[0]

				tmp=self.pad.getmaxyx()[0]
				while actual_height+dt_height>tmp:
					tmp*=2
				self.pad.resize(tmp,width)

				new_pad.overwrite(self.pad,0,0,actual_height,0,actual_height+dt_height-1,width-1)
				actual_height+=dt_height

			self.begin_row=round(self.begin_row*actual_height/self.actual_height)
			self.width=width
			self.actual_height=actual_height

	def update(self):
		height=max(1,min(self.height,self.actual_height))
		self.pad.overwrite(self.stdscr,self.begin_row,0,self.pos_y,self.pos_x,self.pos_y+height-1,self.pos_x+self.width-1)
