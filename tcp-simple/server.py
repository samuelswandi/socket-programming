from socket import *

# Setup server
server_host = "localhost"
server_port = 12001
server_url = (server_host, server_port)
server_socket = socket(AF_INET, SOCK_STREAM)
server_socket.bind(server_url)

# Listen to accept connection
server_socket.listen(1)
print("[Server] Ready to receive")

while True:
    connection_socket, address = server_socket.accept()
    print(f"[Server] Accept connection from {address}")

    message = connection_socket.recv(1024)
    print(f"[Server] receives {message} from {address}")

    modified_message = message.decode().upper()
    connection_socket.send(modified_message.encode())
    connection_socket.close()
