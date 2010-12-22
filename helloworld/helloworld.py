from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

class MainPage(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()

		if user:
			self.response.headers['Content-Type'] = 'text/html'
			self.response.out.write('Hello, webapp World!<br/>')
			self.response.out.write('query string: ' + self.request.query_string + '<br/>')
			self.response.out.write('path: ' + self.request.path + '<br/>')
			
		else:
			self.redirect(users.create_login_url(self.request.uri))

app = webapp.WSGIApplication([('/.*',MainPage)], debug=True)

def main():
	run_wsgi_app(app)

if __name__ == "__main__":
	main()
