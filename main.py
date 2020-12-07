import PySimpleGUI as sg
import ctypes
import re
import fnmatch
import os
import socket
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
		
		#port = values[0]
		#port = int(port)
		break

	#program will not continue if cancel is pressed
	if cont == True:
		port = values[0]
		port = int(port)
		server = socket.socket()
		server.bind((host,port))

		window.close()

		#displays window that shows user which port they are listening on for a few seconds
		message = "Waiting on port " + str(port)
		sentlayout = [[sg.Text(message)]]
		window = sg.Window("",layout=sentlayout,margins=(20,20))

		event, values = window.read(timeout=1)
		#window.close()
		
		server.listen(5)
		
		client, address = server.accept()

		received = client.recv(BUFFER_SIZE).decode()

		file_name, file_size = received.split(SEPARATOR)

		file_name = os.path.basename(file_name)

		file_size = int(file_size)

		currlocation = window.CurrentLocation()
		window.close()
		receivinglayout=[[sg.Text("Recieving file, Please Wait...")]]
		window = sg.Window("",receivinglayout,margins=(20,20),location=currlocation)
		event, values = window.read(timeout=2000)
		
		#window.close()

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
		filesent=True
				
		#window.close()

		if filesent == True:
			donelayout = [[sg.Text("File Recieved Succesfully!")]]

			sg.PopupTimed("File Recieved Succesfully",location=(Width/4,(Height/2)-100),auto_close=True,auto_close_duration=(300000))
	
 


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
					
					print(filename)
					print(len(filename))
				except:
					pass
			print(len(filename))
			if event == "Send" and len(filename) != 0:
				break
			elif event == "Send" and len(filename) == 0:
				print("Error nothing selected")

		filesent=False
		#attempt to send file after file is chosen
		if len(filename) != 0:
			file_size = os.path.getsize(filename)

			sock = socket.socket()
			sock.connect((host, port))
			
			sock.send(f"{filename}{SEPARATOR}{file_size}".encode())

			progress = tqdm.tqdm(range(file_size), "Sending {}".format(filename), unit='B', unit_scale=True, unit_divisor=1024)
			with open(filename, 'rb') as file:
				for _ in progress:
					bytes_read = file.read(BUFFER_SIZE)
					if not bytes_read:
						sock.close()
						break
					sock.sendall(bytes_read)
					progress.update(len(bytes_read))
				print(filename)
			filesent=True

		#window.close()
		if filesent==True:
			endlayout = [[sg.Text("File Sent. Program will now close")]]
			window = sg.Window("Client End",endlayout,margins=(20,20))
			event, values = window.read(timeout = 3000)
			#window.close()


