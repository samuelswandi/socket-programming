from socket import *

# Setup client
host = 'localhost'
port = 12001
url = (host, port)
client_socket = socket(AF_INET, SOCK_STREAM)

# Because its TCP, need to construct connection first with server
client_socket.connect(url)

# Input message that we want to send to server
message = input('input lowercase sentence: ')

# Send mesesage to server url
client_socket.send(message.encode())

# Get repsonse from server
modified_message = client_socket.recv(1024)
print (modified_message.decode())
client_socket.close()
