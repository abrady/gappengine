import base64
import cgi
import Cookie
import email.utils
import hashlib
import hmac
import logging
import os.path
import time
import urllib
#path_to_patched = os.path.join(here, 'lib', 'python2.5', 'site-packages', 'appengine_monkey-0.1dev_r29-py2.5.egg', 'appengine_monkey_files', 'module-replacements', 'httplib.py')
#execfile(path_to_patched, httplib.__dict__)

# import wsgiref.handlers

#from django.utils import simplejson as json
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

FACEBOOK_APP_ID = "166075663433750"
FACEBOOK_APP_SECRET = "be98a62f42aee62500d525f11dfac5f1"


class User(db.Model):
	id = db.StringProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)
	updated = db.DateTimeProperty(auto_now=True)
	name = db.StringProperty(required=True)
	profile_url = db.StringProperty(required=True)
	access_token = db.StringProperty(required=True)


class BaseHandler(webapp.RequestHandler):
	@property
	def current_user(self):
		"""Returns the logged in Facebook user, or None if unconnected."""
		if not hasattr(self, "_current_user"):
			self._current_user = None
			user_id = parse_cookie(self.request.cookies.get("fb_user"))
			if user_id:
				self._current_user = User.get_by_key_name(user_id)
		return self._current_user



class HomeHandler(BaseHandler):
	def get(self):
		path = os.path.join(os.path.dirname(__file__), "oauth.html")
		args = dict(current_user=self.current_user)
		self.response.out.write(template.render(path, args))


class LoginHandler(BaseHandler):
	def get(self):
		verification_code = self.request.get("code")
		args = dict(client_id=FACEBOOK_APP_ID, redirect_uri=self.request.path_url)
		if self.request.get("code"):
			args["client_secret"] = FACEBOOK_APP_SECRET
			args["code"] = self.request.get("code")
			access_str = urllib.urlopen("http://graph.facebook.com/oauth/access_token?" + urllib.urlencode(args)).read()
			logging.root.level = logging.DEBUG
			logging.debug("access str: " + access_str)
			response = cgi.parse_qs(access_str)
			access_token = response["access_token"][-1]

			# Download the user profile and cache a local instance of the
			# basic profile info
			profile = json.load(urllib.urlopen(
				"https://graph.facebook.com/me?" +
				urllib.urlencode(dict(access_token=access_token))))
			user = User(key_name=str(profile["id"]), id=str(profile["id"]),
						name=profile["name"], access_token=access_token,
						profile_url=profile["link"])
			user.put()
			set_cookie(self.response, "fb_user", str(profile["id"]),
					   expires=time.time() + 30 * 86400)
			self.redirect("/")
		else:
			self.redirect(
				"https://graph.facebook.com/oauth/authorize?" +
				urllib.urlencode(args))


class LogoutHandler(BaseHandler):
	def get(self):
		set_cookie(self.response, "fb_user", "", expires=time.time() - 86400)
		self.redirect("/")


def set_cookie(response, name, value, domain=None, path="/", expires=None):
	"""Generates and signs a cookie for the give name/value"""
	timestamp = str(int(time.time()))
	value = base64.b64encode(value)
	signature = cookie_signature(value, timestamp)
	cookie = Cookie.BaseCookie()
	cookie[name] = "|".join([value, timestamp, signature])
	cookie[name]["path"] = path
	if domain: cookie[name]["domain"] = domain
	if expires:
		cookie[name]["expires"] = email.utils.formatdate(
			expires, localtime=False, usegmt=True)
	response.headers._headers.append(("Set-Cookie", cookie.output()[12:]))


def parse_cookie(value):
	"""Parses and verifies a cookie value from set_cookie"""
	
	if not value: return None
	parts = value.split("|")
	if len(parts) != 3: return None
	if cookie_signature(parts[0], parts[1]) != parts[2]:
		logging.warning("Invalid cookie signature %r", value)
		return None
	timestamp = int(parts[1])
	if timestamp < time.time() - 30 * 86400:
		logging.warning("Expired cookie %r", value)
		return None
	try:
		return base64.b64decode(parts[0]).strip()
	except:
		return None


def cookie_signature(*parts):
	"""Generates a cookie signature.

	We use the Facebook app secret since it is different for every app (so
	people using this example don't accidentally all use the same secret).
	"""
	hash = hmac.new(FACEBOOK_APP_SECRET, digestmod=hashlib.sha1)
	for part in parts: hash.update(part)
	return hash.hexdigest()


class TestPage(webapp.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/html'
		self.response.out.write('<head></head><body>hello there!</body>')
			   

def main():
	run_wsgi_app(webapp.WSGIApplication([
		(r"/fb01_oath/", HomeHandler),
		(r"/fb01_oath/auth/login", LoginHandler),
		(r"/fb01_oath/auth/logout", LogoutHandler),
#		('/.*',TestPage),
	]))


if __name__ == "__main__":
	main()
