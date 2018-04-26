#!/usr/bin/python

"""
Save this file as server.py
>>> python server.py 0.0.0.0 8001
serving on 0.0.0.0:8001

or simply

>>> python server.py
Serving on localhost:8000

You can use this to test GET and POST methods.

"""

import SimpleHTTPServer
import SocketServer
import logging
import cgi

import sys


if len(sys.argv) > 2:
    PORT = int(sys.argv[2])
    I = sys.argv[1]
elif len(sys.argv) > 1:
    PORT = int(sys.argv[1])
    I = ""
else:
    PORT = 8000
    I = ""


class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        logging.warning("======= GET STARTED =======")
        logging.warning(self.headers)
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        logging.warning("======= POST STARTED =======")
        logging.warning(self.headers)
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })
        
        output = self.path+"home/victor.ponce/SocialCar/posts/"
        # Begin the response
        self.send_response(200)
        self.end_headers()
        self.wfile.write('Client: %s\n' % str(self.client_address))
        self.wfile.write('User-agent: %s\n' % str(self.headers['user-agent']))
        self.wfile.write('Path: %s\n' % output)
        self.wfile.write('Form data: %s\n' % form)
        
        # Echo back information about what was posted in the form
        logging.warning("======= POST VALUES =======")
        
        ## form customized 
        #for item in form:
        #    logging.warning(item)
        logging.warning("\n")
                
        ## form 1 - form cgi field non indexable
        #for item in form.list:
        #    logging.warning(item)
        #logging.warning("\n")
        
        
        ## form 2 - form cgi field snon indexable
        #for field in form.keys():
        #    field_item = form[field]
        #    if field_item.filename:
        #        # The field contains an uploaded file
        #        file_data = field_item.file.read()
        #        file_len = len(file_data)
        #        del file_data
        #        self.wfile.write('\tUploaded %s as "%s" (%d bytes)\n' % \
        #                (field, field_item.filename, file_len))
        #    else:
        #        # Regular form value
        #        self.wfile.write('\t%s=%s\n' % (field, form[field].value))
        
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
        return

Handler = ServerHandler

httpd = SocketServer.TCPServer(("", PORT), Handler)

print "@rochacbruno Python http server version 0.1 (for testing purposes only)"
print "Serving at: http://%(interface)s:%(port)s" % dict(interface=I or "localhost", port=PORT)
httpd.serve_forever()
