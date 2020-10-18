import os
import re
import socket
import tqdm

IP_REG = '^((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|$)){4}$'
PORT_REG = '^6553[0-5]|655[0-2]\d|65[0-4]\d{2}|6[0-4]\d{3}|5\d{4}|[0-9]\d{0,3}$'
SEPARATOR = '@@@'
BUFFER_SIZE = 4096

choice = 'n'
while choice not in 'sr':
	print('(S)ender or (R)eciever?')
	choice = input()
	while not choice:
		choice = input()
	choice = choice[0].lower()


#	Client Code
if choice == 's':
	print('You have chosen role: "Client/Sender"')

	print('\nPlease enter the IPv4 address that you wish to send to...')
	host = input()

	while re.fullmatch(IP_REG, host) == None:
		print('Invalid IPv4 address, try again...')
		host = input()

	print('\nPlease enter the port that you wish to send to...')
	port = input()

	while re.fullmatch(PORT_REG, port) == None:
			print('Invalid port, try again...')
			port = input()
	
	port = int(port)

	print('\nPlease enter the path/name of the file you with to send...')
	file_name = input()

	while not os.path.isfile(file_name):
		print('File does not exist, try again...')
		file_name = input()

	file_size = os.path.getsize(file_name)

	sock = socket.socket()
	sock.connect((host, port))

	sock.send(f"{file_name}{SEPARATOR}{file_size}".encode())

	progress = tqdm.tqdm(range(file_size), "Sending {}".format(file_name), unit='B', unit_scale=True, unit_divisor=1024)
	with open(file_name, 'rb') as file:
		for _ in progress:
			bytes_read = file.read(BUFFER_SIZE)
			if not bytes_read:
				sock.close()
				break
			sock.sendall(bytes_read)
			progress.update(len(bytes_read))


#	Server Code
else:
	print('You have chosen role: "Server/Receiver"\n')

	host = '0.0.0.0'

	print('\nPlease enter the port that you wish to use...')
	port = input()

	while re.fullmatch(PORT_REG, port) == None:
	    print('Invalid port, try again...')
	    port = input()

	port = int(port)

	server = socket.socket()

	server.bind((host, port))

	print('\nWaiting for connection...')

	server.listen(5)

	client, address = server.accept()

	received = client.recv(BUFFER_SIZE).decode()

	file_name, file_size = received.split(SEPARATOR)

	file_name = os.path.basename(file_name)

	file_size = int(file_size)

	progress = tqdm.tqdm(range(file_size), '\nReceiving {}'.format(file_name), unit='B', unit_scale=True, unit_divisor=1024)

	with open(file_name, 'wb') as file:

		for _ in progress:
			bytes_read = client.recv(BUFFER_SIZE)

			if not bytes_read:
				client.close()
				server.close()
				break

			file.write(bytes_read)

			progress.update(len(bytes_read))

print('Transfer success!')
print('Press any key to exit...')
input()
