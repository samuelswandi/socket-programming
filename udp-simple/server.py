from socket import *

# Setup server
server_host = "localhost"
server_port = 12000
server_url = (server_host, server_port)
server_socket = socket(AF_INET, SOCK_DGRAM)
server_socket.bind(server_url)
print("Server is ready to receive")

while True:
    message, client_address = server_socket.recvfrom(2048)
    print(f"Server receives {message} from {client_address}")
    modified_message = message.decode().upper()
    server_socket.sendto(modified_message.encode(), client_address)
