import socket

def readSocket(s:socket.socket)->bytes:
	length_bytes=s.recv(4)
	if len(length_bytes)!=4:
		return b''
	else:
		rest=int.from_bytes(length_bytes)
		data=b''
		while rest>0:
			new_data=s.recv(rest)
			rest-=len(new_data)
			data+=new_data
		return data

def sendSocket(s:socket.socket,data:bytes):
	length_bytes=len(data).to_bytes(4)
	s.send(length_bytes)
	s.send(data)
