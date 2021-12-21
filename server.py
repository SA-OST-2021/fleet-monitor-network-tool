""" 
A html file server written in python
"""


import socket
import threading
import sys
import time
import pandas as pd
import json
import csv
import os

class HttpServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.content_dir = 'files'
        self.configFilePath = 'files/config.json'
        self.configFileTimestamp = 0
        self.configFileReloadFlag = False

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print("Starting server on {host}:{port}".format(host=self.host, port=self.port))
            self.socket.bind((self.host, self.port))
            print("Server started on port {port}.".format(port=self.port))

        except Exception as e:
            print("Error: Could not bind to port {port}".format(port=self.port))
            self.shutdown()
            sys.exit(1)

        self._listen()

    def shutdown(self):
        try:
            print("Shutting down server")
            self.socket.shutdown(socket.SHUT_RDWR)

        except Exception as e:
            pass # Pass if socket is already closed

    def _generate_headers(self, response_code, size=0):
        header = ''
        if response_code == 200:
            header += 'HTTP/1.1 200 OK\n'
        elif response_code == 404:
            header += 'HTTP/1.1 404 Not Found\n'

        
        header += 'Server: Simple-Python-Server\n'
        header += 'Connection: close\n' # Signal that connection will be closed after completing the request
        header += f'Content-Length: {size+2}\n\n'
        return header 

    def _listen(self):
        self.socket.listen(5)
        while True:
            (client, address) = self.socket.accept()
            #client.settimeout(0)
            time.sleep(0.2)
            print("Recieved connection from {addr}".format(addr=address))
            threading.Thread(target=self._handle_client, args=(client, address)).start()

    def _handle_client(self, client, address):
        PACKET_SIZE = 10000
        while True:
            print("CLIENT",client)
            data = client.recv(PACKET_SIZE).decode() # Recieve data packet from client and decode

            if not data: break

            request_method = data.split(' ')[0]
            print("Method: {m}".format(m=request_method))
            print("Request Body: {b}".format(b=data))

            if request_method == "GET" or request_method == "HEAD":
                # Ex) "GET /index.html" split on space
                file_requested = data.split(' ')[1]

                # If get has parameters ('?'), ignore them
                file_requested =  file_requested.split('?')[0]

                if file_requested == "/":
                    file_requested = "/index.html"

                filepath_to_serve = self.content_dir + file_requested
                print("Serving web page [{fp}]".format(fp=filepath_to_serve))
                self.configFilePath = filepath_to_serve
                self.configFileReloadFlag = False
                print('Config File has been requested, now clear reload flag')

                # Load and Serve files content
                try:
                    f = open(filepath_to_serve, 'rb')
                    if request_method == "GET": # Read only for GET
                        response_data = f.read()
                    f.close()
                    response_header = self._generate_headers(200, len(response_data))

                except Exception as e:
                    print("File not found. Serving 404 page.")
                    response_header = self._generate_headers(404)

                    if request_method == "GET": # Temporary 404 Response Page
                        response_data = b'<html><body><center><h1>Error 404: File not found</h1></center><p>Head back to <a href="/">dry land</a>.</p></body></html>'

                response = response_header.encode()
                if request_method == "GET":
                    response += response_data

                client.send(response)
                client.close()
                break
            if request_method == "POST":
            # Store the incoming json string as csv data
                
                if(self.configFileTimestamp != os.path.getmtime(self.configFilePath)):
                    self.configFileTimestamp = os.path.getmtime(self.configFilePath)
                    self.configFileReloadFlag = True
                    print('Config File has been updated, now set reload flag')
                
                time_now = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
                #time_date = 'Date: {now}\n'.format(now=time_now)
                response_content = json.dumps({'Date': time_now, 'ConfigReload': self.configFileReloadFlag})
                response_headers = self._generate_headers(200, len(response_content))
                response = response_headers + response_content
                client.send(response.encode())
                client.close()
                
                lines = data.splitlines()
                jsondata = json.loads(lines[-1])
                #print(jsondata)
                df = pd.DataFrame(jsondata)
                with open('data.csv', 'a') as f:
                    df.to_csv(f, header=False)
#                     f.write(f"{jsondata}\n")
                
                break
            else:
                print("Unknown HTTP request method: {method}".format(method=request_method))


server = HttpServer("10.3.141.1", 8080)
server.start()