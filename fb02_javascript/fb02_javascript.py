import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../python-sdk/src'))
import facebook
import wsgiref.handlers


from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

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


class HomeHandler(BaseHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), "index.html")
        args = dict(current_user=self.current_user,
                    facebook_app_id=FACEBOOK_APP_ID)
        self.response.out.write(template.render(path, args))


def main():
    run_wsgi_app(webapp.WSGIApplication([(r"/.*", HomeHandler)]))


if __name__ == "__main__":
    main()
