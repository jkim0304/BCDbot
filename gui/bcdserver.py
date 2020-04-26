# # # # # # # # # # # # # # # # # # # # # # # 
# VIEWER FOR SETS DATA                      #
# DESIGNED BY GEOFF                         #
# # # # # # # # # # # # # # # # # # # # # # #

import http.server
import socketserver

PORT = 80

class quietServer(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

with socketserver.TCPServer(("", PORT), quietServer) as httpd:
	print("serving at port", PORT)
	httpd.serve_forever()