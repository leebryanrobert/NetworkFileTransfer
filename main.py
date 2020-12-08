import PySimpleGUI as sg
import ctypes
import re
import fnmatch
import os
from Crypto import Random
from Crypto.Cipher import AES, PKCS1_OAEP 
from Crypto.PublicKey import RSA
import socket
import time
import tqdm


IP_REG = '^((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|$)){4}$'
PORT_REG = '^6553[0-5]|655[0-2]\d|65[0-4]\d{2}|6[0-4]\d{3}|5\d{4}|[0-9]\d{0,3}$'
SEPARATOR = '@@@'
BUFFER_SIZE = 4096

user32 = ctypes.windll.user32
Width = user32.GetSystemMetrics(0)
Height = user32.GetSystemMetrics(1)

sg.theme('DarkPurple4')



layout = [[sg.Button("HOST",size=(20,5))] , [sg.Button("CLIENT", size=(20,5))]]
window = sg.Window("Hello World",layout ,margins =(Width/10,Height/5))
event, values = window.read()
	

if event == "HOST":
	key_pair = RSA.generate(2048, Random.new().read)
	key_export = key_pair.publickey().export_key('PEM')
	print(len(key_export))

	host = '0.0.0.0'
	error=False
	cont = True
	window.close()
	hostlayout = [[sg.Text("Port", size=(5,1)), sg.InputText()], [sg.Submit(), sg.Cancel()]]
	errorlayout = [[sg.Text("Port", size=(5,1)), sg.InputText()], [sg.Text("Error, invalid port number!")], [sg.Submit(), sg.Cancel()]]
	window = sg.Window("host",layout=hostlayout,margins=(200,200))
	while True:
		event, values = window.read()
		if event == sg.WIN_CLOSED or event == "Cancel":
			cont = False
			break

		#input validation for port number
		while re.fullmatch(PORT_REG, values[0]) == None:
			if error==False:
				window.close()
				window = sg.Window("host",layout=errorlayout,margins=(200,200))
			error=True

			if event == "Cancel":
				cont = False
				break
		
			event, values = window.read()

		break

	#program will not continue if cancel is pressed
	if cont == True:
		port = values[0]
		port = int(port)
		server = socket.socket()
		server.bind((host,port))

		window.close()

		#displays window that shows user which port they are listening on for a few seconds
		message = "Listening on: Port {}...".format(port)
		sentlayout = [[sg.Text(message)]]
		window = sg.Window("",layout=sentlayout,margins=(20,20))

		event, values = window.read(timeout=1)
		
		server.listen(5)
		
		client, address = server.accept()

		#Receive and decode filename & size
		received = client.recv(BUFFER_SIZE).decode()
		file_name, file_size = received.split(SEPARATOR)
		file_name = os.path.basename(file_name)
		file_size = int(file_size)

		#Send public key to client
		client.send(key_export)

		#Receive and decrypt session key with RSA private key
		rsa_cipher = PKCS1_OAEP.new(key_pair)
		session_key = rsa_cipher.decrypt(client.recv(256))

		window.close()
		receivinglayout=[[sg.Text("Receiving file, Please Wait...")]]
		window = sg.Window("",receivinglayout,margins=(20,20),location=(Width/2,Height/3))
		event, values = window.read(timeout=1)

		progress = tqdm.tqdm(range(file_size), '\nReceiving {}'.format(file_name), unit='B', unit_scale=True, unit_divisor=1024)

		if not os.path.exists('Downloads'):
			os.makedirs('Downloads')

		with open('Downloads/{}'.format(file_name), 'wb') as file:

			for _ in progress:
				client.send(Random.get_random_bytes(1))
				data = client.recv(BUFFER_SIZE)
				if not data:
					client.close()
					server.close()
					break
				client.send(Random.get_random_bytes(1))
				tag = client.recv(16)
				client.send(Random.get_random_bytes(1))
				nonce = client.recv(16)
				#Create AES cipher from session key
				aes_cipher = AES.new(session_key, AES.MODE_EAX, nonce)
				bytes_read = aes_cipher.decrypt_and_verify(data, tag)

				file.write(bytes_read)

				progress.update(len(bytes_read))

				
		window.close()

		sg.PopupTimed("File Received Succesfully...\nProgram will now close",location=(Width/4,(Height/2)-100),auto_close=True,auto_close_duration=(4))


#code for client side
if event == "CLIENT":
	cont = True
	window.close()
	ipv4error = False
	porterror = False
	
	clientlayout = [[sg.Text("IPv4", size=(5,1)), sg.InputText()], [sg.Text("Port", size=(5,1)), sg.InputText()] ,[sg.Submit(), sg.Cancel()]]
	ipv4errorlayout = [[sg.Text("IPv4", size=(5,1)), sg.InputText()], [sg.Text("Port", size=(5,1)), sg.InputText()], [sg.Text("ipv4 is not a valid ipv4 address")] ,[sg.Submit(), sg.Cancel()]]
	porterrorlayout = [[sg.Text("IPv4", size=(5,1)), sg.InputText()], [sg.Text("Port", size=(5,1)), sg.InputText()], [sg.Text("port is not a valid port number")] ,[sg.Submit(), sg.Cancel()]]
	window = sg.Window("client",clientlayout,margins=(200,200))
	
	#event loop to get ipv4 and port values
	while True:
		event, values = window.read()
		if event == sg.WIN_CLOSED or event == "Cancel":
			cont = False
			break
		
		#checks ipv4 input for a valid ipv4 address
		while re.fullmatch(IP_REG, values[0]) == None:
			if ipv4error == False:
				window.close()
				window = sg.Window("client",ipv4errorlayout,margins=(200,200))
				ipv4error = True
			
			if event == "Cancel":
				cont = False
				break
			event, values = window.read()
		
		if cont == False:
			break
		host = values[0]

		#checks port input for valid port number
		while re.fullmatch(PORT_REG, values[1]) == None:
			if porterror == False:
				window.close()
				window = sg.Window("client",porterrorlayout,margins=(200,200))
				porterror=True

			if event == "Cancel":
				cont = False
				break
			event, values = window.read()
		
		port = values[1]
		port = int(port)
		break

	window.close()

	#only progresses program if ipv4 and port were valid inputs
	if cont == True:
		file_list_column = [
			[
				sg.Text("Image Folder"),
				sg.In(size=(25, 1), enable_events=True, key="-FOLDER-"),
				sg.FolderBrowse(),
				sg.Button("Send")
			],
			[
				sg.Listbox(
					values=[], enable_events=True, size=(40, 20), key="-FILE LIST-"
				)
			],
		]

		layout = [[sg.Column(file_list_column)]]
		window = sg.Window("file select", layout)
		filename = ''
		while True:
			event, values = window.read()
			if event == sg.WIN_CLOSED:
				break
			if event == "-FOLDER-":
				folder = values["-FOLDER-"]
				try:
					# Get list of files in folder
					file_list = os.listdir(folder)
				except:
					file_list = []
				fnames = [
					f
					for f in file_list
					if os.path.isfile(os.path.join(folder, f))
				]
				window["-FILE LIST-"].update(fnames)
			elif event == "-FILE LIST-":  # A file was chosen from the listbox
				try:
					filename = os.path.join(
						values["-FOLDER-"], values["-FILE LIST-"][0]
					)
				except:
					pass

			if event == "Send" and len(filename) != 0:
				break
			elif event == "Send" and len(filename) == 0:
				print("Error nothing selected")

		filesent=False
		#attempt to send file after file is chosen
		if len(filename) != 0:
			#Send filename and size
			file_size = os.path.getsize(filename)
			sock = socket.socket()
			sock.connect((host, port))
			sock.send(f"{filename}{SEPARATOR}{file_size}".encode())

			#Recieve public key
			key_import = RSA.import_key(sock.recv(450))

			#Create session key
			session_key = Random.get_random_bytes(16)

			#Encrypt session key with public RSA key
			rsa_cipher = PKCS1_OAEP.new(key_import)
			session_key_export = rsa_cipher.encrypt(session_key)

			#Send encryped session key
			sock.send(session_key_export)

			progress = tqdm.tqdm(range(file_size), "Sending {}".format(filename), unit='B', unit_scale=True, unit_divisor=1024)
			with open(filename, 'rb') as file:
				for _ in progress:
					bytes_read = file.read(BUFFER_SIZE)
					if not bytes_read:
						sock.close()
						break
					#Create AES cipher for encrypting data
					aes_cipher = AES.new(session_key, AES.MODE_EAX)
					data, tag = aes_cipher.encrypt_and_digest(bytes_read)
					sock.recv(1)
					sock.send(data)
					sock.recv(1)
					sock.send(tag)
					sock.recv(1)
					sock.send(aes_cipher.nonce)
					progress.update(len(bytes_read))
				print(filename)
			filesent=True

		window.close()
		if filesent==True:
			endlayout = [[sg.Text("File Transfer Complete...\nProgram will now close")]]
			window = sg.Window("Client End",endlayout,margins=(20,20))


			event, values = window.read(timeout = 4000)
			window.close()
