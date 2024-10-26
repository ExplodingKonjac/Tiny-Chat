import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_socket.connect(('localhost', 12345))

for i in range(10):
	msg = input()
	client_socket.send(msg.encode())

client_socket.close()
