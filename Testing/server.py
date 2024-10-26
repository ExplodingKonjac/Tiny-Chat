import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.bind(('localhost', 12345))

server_socket.listen(1)

print("Waiting...\n")

client_socket, addr = server_socket.accept()
print(f"Connection: {addr}")

for i in range(10):
	data = client_socket.recv(1024)
	print(f"Data #{i}: {data.decode()}\n")

client_socket.close()
server_socket.close()
