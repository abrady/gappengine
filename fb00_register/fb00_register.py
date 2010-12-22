from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

class RegisterPage(webapp.RequestHandler):
	def get(self):
		fb_iframe = """<iframe src='http://www.facebook.com/plugins/registration.php?client_id=166075663433750&redirect_uri=http%3A%2F%2Fdrinkbot9000.appspot.com%2Ffb00_register%2Fregistered&
		fields=name,birthday,gender,location,email'
        scrolling='auto'
        frameborder='no'
        style='border:none'
        allowTransparency='true'
        width='100%'
        height='330'>
		</iframe>"""		
		self.response.headers['Content-Type'] = 'text/html'
		self.response.out.write('fb frame for registering:')
		self.response.out.write(fb_iframe)
		self.response.out.write('query string: ' + self.request.query_string + '<br/>')
		self.response.out.write('path: ' + self.request.path + '<br/>')


class RegisteredPage(webapp.RequestHandler):
	def get(self):
			self.response.headers['Content-Type'] = 'text/html'
			self.response.out.write('<head></head><body>')
			self.response.out.write('registered via facebook!<br/>')
			self.response.out.write('query string: ' + self.request.query_string + '<br/>')
			self.response.out.write('path: ' + self.request.path + '<br/>')
			self.response.out.write('</body>')			
		

app = webapp.WSGIApplication(
	[
	('/.*registered',RegisteredPage),
	('/.*',RegisterPage)
	], debug=True)

def main():
	run_wsgi_app(app)

if __name__ == "__main__":
	main()

