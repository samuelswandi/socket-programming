from socket import *

# Setup client
host = 'localhost'
port = 12000
url = (host, port)
client_socket = socket(AF_INET, SOCK_DGRAM)

# Input message that we want to send to server
message = input('input lowercase sentence: ')

# Send mesesage to server url
client_socket.sendto(message.encode(), url)

# Get repsonse from server
modified_message, server_address = client_socket.recvfrom(2046)
print (modified_message.decode())
client_socket.close()
