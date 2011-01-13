import base64
import urlparse
import Cookie
import email.utils
import hashlib
import hmac
import os.path
import time
import urllib2
import urllib # for urlencode
import os.path
import sys
import logging
import inspect
from pprint import pformat
import json
import wsgiref.handlers

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

sys.path.append(os.path.join(os.path.dirname(__file__), '../python-sdk/src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../common'))
import MultiPartForm # in common
import facebook

FACEBOOK_APP_ID = "166075663433750"
FACEBOOK_APP_SECRET = "be98a62f42aee62500d525f11dfac5f1"
WEB_ROOT = "/" + os.path.splitext(os.path.basename('d:/abs/gappengine/fb01_oath/fb01_oath.py'))[0] + "/"


class User(db.Model):
    id = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    name = db.StringProperty(required=True)
    profile_url = db.StringProperty(required=True)
    access_token = db.StringProperty(required=True)

class GraphObj:
    """Helper so that I can lazily use a.x for getting graph objects instead of a['x']
    """
    def __init__(self, json_obj):
        for k in json_obj['data'].keys():
            setattr(self,k,json_obj[k])

def base64_decode(s):
    """helper to properly pad the strings for base64 decode
    """
    if(len(s)%4 != 0):
        s += '='*(4-len(s)%4)
    s = s.encode('ascii') # otherwise 'translate' fails below
    return base64.urlsafe_b64decode(s) 
    

class BaseHandler(webapp.RequestHandler):
    """Provides access to the active Facebook user in self.current_user

    The property is lazy-loaded on first access, using the cookie saved
    by the Facebook JavaScript SDK to determine the user ID of the active
    user. See http://developers.facebook.com/docs/authentication/ for
    more information.
    """


    @property
    def current_user(self):
        if not hasattr(self, "_current_user"):
            self._current_user = None
            signed_req = self.request.get('signed_request')
            logging.debug('signed_req:' + signed_req)
            (encoded_sig, payload) = signed_req.split('.')
            sig = base64_decode(encoded_sig)
            data_str = base64_decode(payload)
            #logging.debug("(sig,payload) = (%s,%s)" % (sig,data_str))
            data = facebook._parse_json(data_str)
            
            if data['user_id']:
                # Store a local instance of the user data so we don't need
                # a round-trip to Facebook on every request
                user = User.get_by_key_name(data['user_id'])
                access_token = data['oauth_token']
                if not user:
                    logging.debug("no current user in db. adding user of id %s, access_token:%s" % (data['user_id'], access_token))
                    graph = facebook.GraphAPI(access_token)
                    profile = graph.get_object("me")
                    user = User(key_name=str(profile["id"]),
                                id=str(profile["id"]),
                                name=profile["name"],
                                profile_url=profile["link"],
                                access_token=access_token)
                    user.put()
                elif user.access_token != access_token:
                    logging.debug("new access token for user %s(%s): %s" % (user.name,data['user_id'],access_token))
                    user.access_token = access_token
                    user.put()
                self._current_user = user            
        return self._current_user
    

    @property
    def graph(self):
        """Returns a Graph API client for the current user."""
        if not hasattr(self, "_graph"):
            if self.current_user:
                self._graph = facebook.GraphAPI(self.current_user.access_token)
            else:
                self._graph = facebook.GraphAPI()
        return self._graph

    def graph_connections(self,path):
        return self.graph.get_connctions(self.current_user.id,path)

    def graph_put_file(self,path, argname, filename, file, **post_args):
        """put a file to facebook.
        - argname : api name, probably 'source'
        - filename: name of file itself, i.e. foo.jpg
        """
        form = MultipartForm.MultiPartForm()
        form.add_field('access_token', self.current_user.access_token)
        for a in post_args:
            logging.debug("putting arg %s:%s" % (a,post_args[a]))
            form.add_field(a, post_args[a])
        form.add_file(argname,filename,file)
        req = urllib2.Request('https://graph.facebook.com/' + path)
        body = str(form)
        req.add_header('Content-type', form.get_content_type())
        req.add_header('Content-length', len(body))
        req.add_data(body)
        s = urllib2.urlopen(req).read()
        return facebook._parse_json(s)


    def graph_url(self,path,args=None):
        """get an url for opening a location on the graph. not all objects are JSON-able (like profile pictures
        """
        if not args:
            args = {}
        if self.current_user.access_token:
                args["access_token"] = self.current_user.access_token
        return "https://graph.facebook.com/" + path + "?" + urllib.urlencode(args)
        
    def html_graph_pic(self,obj_name):
        """Helper for making the picture img html for a graph object. i.e. album/picture or me/picture
        """
        path =  obj_name + '/picture'
        return "<img src='" + self.graph_url(path) + "'/>"


class HomeHandler(BaseHandler):
    def post(self):
        #NOTE: remove
        logging.root.level = logging.DEBUG
        #logging.debug("environ: " + pformat(self.request.environ))
        dbg_str = ""

        args = dict(current_user=self.current_user,
                    facebook_app_id=FACEBOOK_APP_ID,
                    )
        
        if self.current_user:
            logging.debug("current user: %s(%s), access_token:%s" % (self.current_user.name,self.current_user.id,self.current_user.access_token))

            albums = self.graph.get_connections('me','albums')
            args['albums'] = albums
            dbg_str += "<br>added %i albums" % len(albums)

        args['dbg_str'] = dbg_str
        
        path = os.path.join(os.path.dirname(__file__), "index.html")
        self.response.out.write(template.render(path, args))


class PhotoGrabbedHandler(BaseHandler):
    """This class grabs a picture from a friend and re-uploads it to the destination album
    """

    def graph_put_file(self,path, argname, filename, file, **post_args):
        """put a file to facebook.
        - argname : api name, probably 'source'
        - filename: name of file itself, i.e. foo.jpg
        """
        form = MultipartForm.MultiPartForm()
        form.add_field('access_token', self.current_user.access_token)
        for a in post_args:
            logging.debug("putting arg %s:%s" % (a,post_args[a]))
            form.add_field(a, post_args[a])
        form.add_file(argname,filename,file)
        req = urllib2.Request('https://graph.facebook.com/' + path)
        body = str(form)
        req.add_header('Content-type', form.get_content_type())
        req.add_header('Content-length', len(body))
        req.add_data(body)
        s = urllib2.urlopen(req).read()
        return facebook._parse_json(s)

    
    def get(self):
        logging.root.level = logging.DEBUG
        
        err = ""
        if not self.current_user:
            err = "no current user found. "
        album_id = self.request.get('dst_album',None)
        if not album_id:
            err += "couldn't get album id."
        src_photo_id = self.request.get('photo_id',None)
        if not src_photo_id:
            err += "couldn't get photo id"
        if len(err):
            logging.debug("error %s grabbing photo" % err)
            self.error(500)
            return


        album = self.graph.get_object(album_id) # NOTE: cache this
        pic = 
        self.response.out.write(template.render(path, args))

        
        

class AlbumHandler(BaseHandler):
    """Albums player has chosen to merge
    """


def main():
    run_wsgi_app(webapp.WSGIApplication([
#        (r"/.*/tab_admin/", TabAdminHandler),
#        (r"/.*/tab/", TabHandler,
        (r"/.*photo_grabbed",  PhotoGrabbedHandler),
        (r"/.*album_selected", AlbumSelectedHandler),
        (r"/.*", HomeHandler)
        ]))


if __name__ == "__main__":
    main()

# useful graph params:
# - until, since (a unix timestamp or any date accepted by strtotime): https://graph.facebook.com/search?until=yesterday&q=orange

# example canvas signed_request
# vlXgu64BQGFSQrY0ZcJBZASMvYvTHu9GQ0YM9rjPSso.eyJhbGdvcml0aG0iOiJITUFDLVNIQTI1NiIsIjAiOiJwYXlsb2FkIn0
# 9z3V9dHr4twGjZ3E6DMLgMpRMZfDjwbm-2QHlRqEwM4.eyJhbGdvcml0aG0iOiJITUFDLVNIQTI1NiIsImV4cGlyZXMiOjEyOTQyOTAwMDAsImlzc3VlZF9hdCI6MTI5NDI4MzMwMywib2F1dGhfdG9rZW4iOiIxNjYwNzU2NjM0MzM3NTB8Mi5YOFlhX1BPNnNSajFxMThualhXM1RRX18uMzYwMC4xMjk0MjkwMDAwLTEwMDAwMDYzMTEzODc1NHxvUkprY3NvMW5DcDRUeG4wdTg3UTJCWUNWMU0iLCJ1c2VyIjp7ImxvY2FsZSI6ImVuX1VTIiwiY291bnRyeSI6InVzIn0sInVzZXJfaWQiOiIxMDAwMDA2MzExMzg3NTQifQ
