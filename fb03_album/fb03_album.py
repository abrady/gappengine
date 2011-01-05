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
sys.path.append(os.path.join(os.path.dirname(__file__), '../python-sdk/src'))
import facebook
import wsgiref.handlers

import logging
import inspect
from pprint import pformat

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

import MultiPartForm

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
            cookie = facebook.get_user_from_cookie(
                self.request.cookies, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET)
            if cookie:
                # Store a local instance of the user data so we don't need
                # a round-trip to Facebook on every request
                user = User.get_by_key_name(cookie["uid"])
                if not user:
                    graph = facebook.GraphAPI(cookie["access_token"])
                    profile = graph.get_object("me")
                    user = User(key_name=str(profile["id"]),
                                id=str(profile["id"]),
                                name=profile["name"],
                                profile_url=profile["link"],
                                access_token=cookie["access_token"])
                    user.put()
                elif user.access_token != cookie["access_token"]:
                    user.access_token = cookie["access_token"]
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


class HomeHandler(BaseHandler):
    def get(self):
        #NOTE: remove
        logging.root.level = logging.DEBUG
        logging.debug("HomeHandler")

        body_str = ""
        if self.current_user:
            logging.debug("current user: %s(%s)" % (self.current_user.name,self.current_user.id))

            # get the user's albums
            req = self.graph_connections("albums")
            user_albums = req['data']
            logging.debug("%i albums" % len(user_albums))
            album_meta = {}
            for album in user_albums:
                logging.debug("album %s(%s): num pics %s" % (album['name'],album['id'],album['count']))

            # friend albums
            albums = []
            friends = self.graph.get_connections("friends")
            for friend in friends:
                friend_albums = self.graph.get_connections(friend['id'],'albums')
                for album in friend_albums:
                    logging.debug("album %s(%s): num pics %s" % (album['name'],album['id'],album['count']))
                    # blah blah
                albums.extend(friend_albums)

            # look for matches
            album_connections_cache = {}
            for user_album in user_albums:
                matching_albums = []
                for friend_album in albums:
                    if album_match(user_album, friend_album):
                        matching_albums.append(friend_album)

                if len(matching_albums):
                    s = "matched albums with %s." % user_album['name']
                    for a in matching_albums:
                        s += "name: " + a['name'] + ','
                    logging.debug(s)
                    # okay, now make an album with all those photos
                    album_req = self.graph.put_object(self.current_user.id, "albums",name="album based off of %s" % user_album['name'])
                    album_id = album_req['data']['id']
                    matching_albums.append(user_album)
                    for album in matching_albums:
                        album_id = album['data']['id']
                        if album_connections_cache.has_key(album_id):
                            photos = album_connections_cache[album_id]
                        else:
                            photos = self.graph.get_connctions(album_id,"photos")
                            album_connections_cache[album_id] = photos
                            
                        for photo in photos['data']['images']:
                            self.graph.put_object(album_id,"photos",source=photo['source'])
                            
                            
            
        path = os.path.join(os.path.dirname(__file__), "index.html")
        args = dict(current_user=self.current_user,
                    facebook_app_id=FACEBOOK_APP_ID,
                    body_str=body_str
                    )
        self.response.out.write(template.render(path, args))


def album_match(a,b):
    """TODO: fuzzy logic here to match two user albums. for now return true
    """
    return True


def main():
    run_wsgi_app(webapp.WSGIApplication([(r"/.*", HomeHandler)]))


if __name__ == "__main__":
    main()

# useful graph params:
# - until, since (a unix timestamp or any date accepted by strtotime): https://graph.facebook.com/search?until=yesterday&q=orange


# example album connected to test account: 
# {
#    "data": [
#       {1
#          "id": "175254195838950",
#          "from": {
#             "name": "Bobby McGee",
#             "id": "100000631138754"
#          },
#          "name": "Sake Bomb Night",
#          "location": "Miyake's",
#          "link": "http://www.facebook.com/album.php?aid=38932&id=100000631138754",
#          "privacy": "friends-of-friends",
#          "count": 5,
#          "type": "normal",
#          "created_time": "2010-12-25T23:26:12+0000",
#          "updated_time": "2010-12-25T23:26:31+0000"
#       },
#       {
#          "id": "173847555979614",
#          "from": {
#             "name": "Bobby McGee",
#             "id": "100000631138754"
#          },
#          "name": "Profile Pictures",
#          "link": "http://www.facebook.com/album.php?aid=38157&id=100000631138754",
#          "privacy": "everyone",
#          "count": 1,
#          "type": "profile",
#          "created_time": "2010-12-21T01:19:19+0000",
#          "updated_time": "2010-12-21T01:19:21+0000"
#       }
#    ],
#    "paging": {
#       "previous": "https://graph.facebook.com/me/albums?access_token=2227470867%7C2.aQgMs0SLmifnIiJKM1MvQw__.3600.1293609600-100000631138754%7CoWNbMt1O-H8cKNDz2NPUmEBKh0c&limit=25&since=2010-12-25T23%3A26%3A12%2B0000",
#       "next": "https://graph.facebook.com/me/albums?access_token=2227470867%7C2.aQgMs0SLmifnIiJKM1MvQw__.3600.1293609600-100000631138754%7CoWNbMt1O-H8cKNDz2NPUmEBKh0c&limit=25&until=2010-12-21T01%3A19%3A18%2B0000"
#    }
# }


# example album from Coke: https://graph.facebook.com/99394368305/photos?access_token=2227470867|2.aQgMs0SLmifnIiJKM1MvQw__.3600.1293609600-100000631138754|oWNbMt1O-H8cKNDz2NPUmEBKh0c
# {
#    "data": [
#       {
#          "id": "110516463305",
#          "from": {
#             "name": "Coca-Cola",
#             "category": "Company",
#             "id": "40796308305"
#          },
#          "name": "Random Coke Fact: Coca-Cola translated to Chinese means \u201cDelicious Happiness\u201d.",
#          "picture": "http://photos-h.ak.fbcdn.net/hphotos-ak-snc1/hs195.snc1/6570_110516463305_40796308305_2143765_6253354_s.jpg",
#          "source": "http://sphotos.ak.fbcdn.net/hphotos-ak-snc1/hs195.snc1/6570_110516463305_40796308305_2143765_6253354_n.jpg",
#          "height": 604,
#          "width": 603,
#          "images": [
#             {
#                "height": 604,
#                "width": 603,
#                "source": "http://sphotos.ak.fbcdn.net/hphotos-ak-snc1/hs195.snc1/6570_110516463305_40796308305_2143765_6253354_n.jpg"
#             },
#             {
#                "height": 180,
#                "width": 179,
#                "source": "http://photos-h.ak.fbcdn.net/hphotos-ak-snc1/hs195.snc1/6570_110516463305_40796308305_2143765_6253354_a.jpg"
#             },
#             {
#                "height": 130,
#                "width": 129,
#                "source": "http://photos-h.ak.fbcdn.net/hphotos-ak-snc1/hs195.snc1/6570_110516463305_40796308305_2143765_6253354_s.jpg"
#             },
#             {
#                "height": 75,
#                "width": 75,
#                "source": "http://photos-h.ak.fbcdn.net/hphotos-ak-snc1/hs195.snc1/6570_110516463305_40796308305_2143765_6253354_t.jpg"
#             }
#          ],
#          "link": "http://www.facebook.com/photo.php?pid=2143765&id=40796308305",
#          "icon": "http://static.ak.fbcdn.net/rsrc.php/yz/r/StEh3RhPvjk.gif",
#          "created_time": "2009-07-26T12:33:14+0000",
#          "position": 1,
#          "updated_time": "2009-07-26T12:33:14+0000",
# ...


######################################################################
# Scratch area
######################################################################

# albums attrs: '['__class__',
#  '__cmp__',
#  '__contains__',
#  '__delattr__',
#  '__delitem__',
#  '__doc__',
#  '__eq__',
#  '__ge__',
#  '__getattribute__',
#  '__getitem__',
#  '__gt__',
#  '__hash__',
#  '__init__',
#  '__iter__',
#  '__le__',
#  '__len__',
#  '__lt__',
#  '__ne__',
#  '__new__',
#  '__reduce__',
#  '__reduce_ex__',
#  '__repr__',
#  '__setattr__',
#  '__setitem__',
#  '__str__',
#  'clear',
#  'copy',
#  'fromkeys',
#  'get',
#  'has_key',
#  'items',
#  'iteritems',
#  'iterkeys',
#  'itervalues',
#  'keys',
#  'pop',
#  'popitem',
#  'setdefault',
#  'update',
#  'values']' data: '{u'data': []}'

