import curses
import wcwidth

from typing import Sequence

color_dict:dict[tuple[int,int],int]={}

def color(fg:int,bg:int)->int:
	if (fg,bg) in color_dict.keys():
		return curses.color_pair(color_dict[(fg,bg)])
	else:
		x=len(color_dict)+1
		curses.init_pair(x,fg,bg)
		color_dict[(fg,bg)]=x
		return curses.color_pair(x)

def drawText(text_seq:Sequence[str|int],width:int)->curses.window:
	pad=curses.newpad(1,width+1)
	cur_attr=0
	cur_y=0
	cur_x=0

	for elem in text_seq:
		if isinstance(elem,str):
			for ch in elem:
				wc=wcwidth.wcwidth(ch)
				if ch=='\n' or cur_x+wc>width:
					cur_y+=1
					cur_x=0
					if cur_y>=pad.getmaxyx()[0]:
						pad.resize(cur_y*2,width+1)
				if ch!='\n':
					pad.addch(cur_y,cur_x,ch,cur_attr)
					cur_x+=wc
		else:
			cur_attr=elem

	if cur_x==width:
		cur_y+=1
	pad.resize(cur_y+1,width)
	return pad

def getCursorPos(text_seq:Sequence[str],offset:int,width:int)->tuple[int,int]:
	cur_x=0
	cur_y=0

	for elem in text_seq:
		if not isinstance(elem,str):
			continue
		for ch in elem:
			if ch=='\n':
				cur_y+=1
				cur_x=0
			else:
				wc=wcwidth.wcwidth(ch)
				if cur_x+wc>width:
					cur_y+=1
					cur_x=0
				cur_x+=wc
			if cur_x==width:
				cur_y+=1
				cur_x=0
			offset-=1
			if offset==0:
				return (cur_y,cur_x)

	return (cur_y,cur_x)
