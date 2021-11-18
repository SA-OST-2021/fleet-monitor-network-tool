""" 
A html file server written in python
"""


import socket
import threading
import sys
import time

class HttpServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.content_dir = 'files'

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

    def _generate_headers(self, response_code):
        header = ''
        if response_code == 200:
            header += 'HTTP/1.1 200 OK\n'
        elif response_code == 404:
            header += 'HTTP/1.1 404 Not Found\n'

        time_now = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        header += 'Date: {now}\n'.format(now=time_now)
        header += 'Server: Simple-Python-Server\n'
        header += 'Connection: close\n\n' # Signal that connection will be closed after completing the request
        return header

    def _listen(self):
        self.socket.listen(5)
        while True:
            (client, address) = self.socket.accept()
            #client.settimeout(0)
            print("Recieved connection from {addr}".format(addr=address))
            threading.Thread(target=self._handle_client, args=(client, address)).start()

    def _handle_client(self, client, address):
        PACKET_SIZE = 1024
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

                # Load and Serve files content
                try:
                    f = open(filepath_to_serve, 'rb')
                    if request_method == "GET": # Read only for GET
                        response_data = f.read()
                    f.close()
                    response_header = self._generate_headers(200)

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
                json_string = data.split('\r\n')[-1]
                csv_string = json_to_csv(json_string)
                with open('data.csv', 'w') as f:
                    f.write(csv_string)
                response_headers = self._generate_headers(200)
                response_content = json.dumps({'message': 'OK'})
                response = response_headers + response_content
                client.send(response.encode())
                client.close()
            else:
                print("Unknown HTTP request method: {method}".format(method=request_method))


def json_to_csv(json_string):
    json_data = json.loads(json_string)
    csv_data = ""
    for i in range(len(json_data)):
        for j in range(len(json_data[i])):
            csv_data += str(json_data[i][j])
            if j != len(json_data[i])-1:
                csv_data += ","
        csv_data += "\n"
    return csv_data

server = HttpServer('', 8080)
server.start()