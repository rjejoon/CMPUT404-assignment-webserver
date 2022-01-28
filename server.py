#  coding: utf-8 

# Copyright 2022 Abram Hindle, Eddie Antonio Santos, Jejoon Ryu
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2022 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/

import socketserver
import os
import datetime


HTTP_VER = 1.1
BUFFER_SIZE = 4096
VALID_REQUEST_METHODS = ['GET']

class MyWebServer(socketserver.BaseRequestHandler):

    def handle(self):
        self.data = self.request.recv(BUFFER_SIZE)
        request_dict = self.parse_http_request(self.data.decode('utf-8'))
        req_method, req_path, req_http_ver = request_dict["Request"].split(' ')

        if not self.is_valid_req_method(req_method):
            self.send_405()
        elif not self.is_valid_req_dirpath(req_path):
            self.send_301(req_path)
        elif not self.is_valid_path(req_path):
            self.send_404()
        else:
            self.send_200(req_path)


    def parse_http_request(self, request: str) -> dict:
        '''
        Parse an HTTP request message and return a dictionary of header lines.
        '''
        lines = request.strip().split('\r\n')

        request_dict = dict()
        request_dict["Request"] = lines[0]
        for line in lines[1:]:
            header, value = line.split(': ')
            request_dict[header] = value

        return request_dict


    def http_response(self, status: int, headers: list, res_entity_body='') -> str:
        '''
        Given a status code, header lines, and entity body, 
        return an http response message.
        '''
        status_phrase_dict = {
            200: 'OK', 
            301: 'Moved Permanently',
            404: 'Not Found', 
            405: 'Method Not Allowed',
        }

        response = []
        status_line = f'HTTP/{HTTP_VER} {status} {status_phrase_dict[status]}'
        response.append(status_line)
        response.extend(headers)
        response.append('\r\n')
        
        return '\r\n'.join(response) + res_entity_body
        

    def get_abs_root_dir(self) -> str:
        '''
        Return an absolute root directory of the web server
        '''
        return os.path.join(os.path.abspath(os.path.dirname(__file__)), 'www')


    def is_valid_path(self, path: str) -> str:
        '''
        Return True if the given normalized path exists and 
        is located in the root of the server.
        '''
        abs_path = self.get_abs_path_of(path)
        norm_path = os.path.normpath(abs_path)
        abs_root_dir = self.get_abs_root_dir()
        return os.path.commonpath([norm_path, abs_root_dir]) == abs_root_dir and os.path.exists(abs_path)


    def get_abs_path_of(self, path: str) -> str:
        '''
        Return an absolute path to the given path.
        '''
        if path[-1] == '/':
            path += 'index.html'
        return os.path.join(self.get_abs_root_dir(), path[1:])
        

    def get_current_rfc_date_str(self) -> str:
        now = datetime.datetime.utcnow()
        return now.strftime("%a, %d %b %Y %H:%M:%S GMT")


    def is_valid_req_method(self, req_method: str) -> bool:
        '''
        Return True if the server can handle the given http request method.
        '''
        return req_method in VALID_REQUEST_METHODS 

    
    def is_valid_req_dirpath(self, req_path: str) -> bool:
        '''
        Return True if the path (may not exist) is a directory and ends with '/'.
        Otherwise, return False.
        '''
        if req_path[-1] == '/':
            return True
        return '.' in req_path.split(os.path.sep)[-1]


    def send_200(self, req_path: str):
        '''
        Send a 200 http response message back to the client with 
        appropriate header lines and an entity body.
        '''

        res_status = 200
        header_lines = []
        res_entity_body = ''

        abs_req_path = self.get_abs_path_of(req_path)
        with open(abs_req_path, 'r') as f:
            ext = abs_req_path.split('.')[-1]
            res_entity_body = f.read()
            content_len = len(res_entity_body)

        header_lines.append(f'Content-Length: {content_len}')
        header_lines.append(f'Content-Type: text/{ext}')
        header_lines.append(f'Date: {self.get_current_rfc_date_str()}')
        header_lines.append(f'Connection: close')

        res_msg = self.http_response(res_status, header_lines, res_entity_body)

        self.request.send(bytearray(res_msg,'utf-8'))


    def send_301(self, req_path: str):
        '''
        Send a 301 http response message back to the client with
        appropriate header lines.
        '''
        status = 301
        header_lines = []

        addr, port = self.server.server_address 

        # handles dir path that does not terminate with /
        forward_url = f'http://{addr}:{port}{req_path}/'
        header_lines.append(f'Location: {forward_url}')
        header_lines.append(f'Date: {self.get_current_rfc_date_str()}')
        header_lines.append(f'Connection: close')
        res_msg = self.http_response(status, header_lines)

        self.request.send(bytearray(res_msg,'utf-8'))


    def send_404(self):
        '''
        Send a 404 http response message back to the client with
        appropriate header lines.
        '''
        status = 404
        header_lines = []
        entity_body = ''

        header_lines.append(f'Date: {self.get_current_rfc_date_str()}')
        header_lines.append(f'Connection: close')
        res_msg = self.http_response(status, header_lines, entity_body)

        self.request.send(bytearray(res_msg,'utf-8'))


    def send_405(self):
        status = 405
        header_lines = []

        header_lines.append(f'Date: {self.get_current_rfc_date_str()}')
        # server only accepts GET request
        header_lines.append(f'Allow: {", ".join(VALID_REQUEST_METHODS)}')
        res_msg = self.http_response(status, header_lines)

        self.request.send(bytearray(res_msg,'utf-8'))



if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
