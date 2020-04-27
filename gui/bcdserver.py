# # # # # # # # # # # # # # # # # # # # # # # 
# VIEWER FOR SETS DATA                      #
# DESIGNED BY GEOFF                         #
# DONT USE  UNSTABLE                        #
# # # # # # # # # # # # # # # # # # # # # # #

import http.server
import socketserver

PORT = 80

class quietServer(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
try:
	with socketserver.TCPServer(("", PORT), quietServer) as httpd:
		print("serving at port", PORT)
		httpd.serve_forever()
except Exception:
	print(Exception)