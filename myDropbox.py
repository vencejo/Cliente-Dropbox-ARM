#!/usr/bin/python
import locale
import os
import pprint
import shlex
import sys
from dropbox import client, rest, session
import time
import datetime

APP_KEY = 'o05x3rxfamtxc74'
APP_SECRET = 'www8ibf6jja0z6q'
ACCESS_TYPE = 'dropbox'  # should be 'dropbox' or 'app_folder' as configured for your app

class Dropbox():
    def __init__(self, app_key, app_secret):
        self.sess = StoredSession(app_key, app_secret, access_type=ACCESS_TYPE)
        self.api_client = client.DropboxClient(self.sess)
        self.sess.load_creds()

            
    def ls(self,path):
        """ Devuelve una lista de tuplas la siguiente info de los archivos o
        carpetas de la ruta seleccionada : [(ruta, tipo, tiempo), (r,t,t), ..] """
        resp = self.api_client.metadata(path)
        listOfFiles = []
        if 'contents' in resp:
            for f in resp['contents']:
                ruta = os.path.basename(f['path'])
                tipo = 'directorio' if f['is_dir'] else 'archivo'
                tiempo = int(time.mktime(datetime.datetime.strptime(f['modified'], "%a, %d %b %Y %H:%M:%S +0000").timetuple())) 
                listOfFiles.append((ruta, tipo, tiempo))
        return listOfFiles


    def mkdir(self, path):
        """create a new directory"""
        self.api_client.file_create_folder( "/" + path)

 
    def rm(self, path):
        self.api_client.file_delete( "/" + path)

  
    def get(self, from_path, to_path):
        to_file = open(os.path.expanduser(to_path), "wb")
        f, metadata = self.api_client.get_file_and_metadata( from_path)
        print 'Metadata:', metadata
        to_file.write(f.read())


    def put(self, from_path, to_path):
        from_file = open(os.path.expanduser(from_path), "rb")
        self.api_client.put_file("/" + to_path, from_file)

    def isDir(self, path):
        details=self.api_client.metadata( "/" + path)
        return details.get('is_dir')
       
            

class StoredSession(session.DropboxSession):
    """a wrapper around DropboxSession that stores a token to a file on disk"""
    TOKEN_FILE = "token_store.txt"

    def load_creds(self):
        try:
            stored_creds = open(self.TOKEN_FILE).read()
            self.set_token(*stored_creds.split('|'))
            print "[loaded access token]"
        except IOError:
            pass # don't worry if it's not there

    def write_creds(self, token):
        f = open(self.TOKEN_FILE, 'w')
        f.write("|".join([token.key, token.secret]))
        f.close()

    def delete_creds(self):
        os.unlink(self.TOKEN_FILE)

    def link(self):
        request_token = self.obtain_request_token()
        url = self.build_authorize_url(request_token)
        print "url:", url
        print "Please authorize in the browser. After you're done, press enter."
        raw_input()

        self.obtain_access_token(request_token)
        self.write_creds(self.token)

    def unlink(self):
        self.delete_creds()
        session.DropboxSession.unlink(self)
        
        
def connect():
    if APP_KEY == '' or APP_SECRET == '':
        exit("You need to set your APP_KEY and APP_SECRET!")
    d = Dropbox(APP_KEY, APP_SECRET)
    return d
    
if __name__ == '__main__':
    d = connect()
    print d.ls('/')
    d.get("/Comenzar.pdf", "/home/pi/Desktop/ClienteDropbox/Nube/Carpeta2/Nuevo2/Comenzar.pdf")
