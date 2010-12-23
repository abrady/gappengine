import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

def get_subdirs(dir):
    return [name for name in os.listdir(dir)
            if os.path.isdir(os.path.join(dir, name))]


class MainPage(webapp.RequestHandler):
	def get(self):
#		self.response.out.write('foo')
		path = os.path.join(os.path.dirname(__file__), "home.template")
		subdirs = get_subdirs(os.path.dirname(__file__))
		args = dict(linkdirs=subdirs)
		self.response.out.write(template.render(path, args))

  

app = webapp.WSGIApplication([('/.*',MainPage)], debug=True)

def main():
	run_wsgi_app(app)

if __name__ == "__main__":
	main()
