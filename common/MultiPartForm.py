import itertools
import time
import mimetools
import mimetypes
from cStringIO import StringIO
import urllib
import urllib2
import os
import random
import logging

class MultiPartForm(object):
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = 'abrady.xen.prgmr.com' +  '.' + str(time.time())
        # hmm, os.getpid() doesn't work either
        # mimetools.choose_boundary() : doesn't work in gapp engine socket.gethostname
        return

    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name.encode('ascii'), value.encode('ascii')))
        return

    def add_file(self, fieldname, filename, fileHandle, mimetype=None):
        """Add a file to be uploaded."""
        body = fileHandle.read()
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        self.files.append((fieldname, filename, mimetype, body))
        return

    def __str__(self):
        """Return a string representing the form data, including attached files."""
        # Build a list of lists, each containing "lines" of the
        # request.  Each part is separated by a boundary string.
        # Once the list is built, return a string where each
        # line is separated by '\r\n'.  
        parts = []
        part_boundary = '--' + self.boundary

        # Add the form fields
        parts.extend(
            [ part_boundary,
              'Content-Disposition: form-data; name="%s"' % name,
              '',
              value,
            ]
            for name, value in self.form_fields
            )

        # Add the files to upload
        parts.extend(
            [ part_boundary,
              ('Content-Disposition: file; name="%s"; filename="%s"' % \
                 (field_name, filename)).encode('ascii'),
              'Content-Type: %s' % content_type,
              '',
              body,
            ]
            for field_name, filename, content_type, body in self.files
            )

        # Flatten the list and add closing boundary marker,
        # then return CR+LF separated data
        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')

        # AB: binary data in python is strange. as soon as you get a str mixed with a unicode object it starts encoding everything
        # which screws up any 'str' objects you have that aren't actually valid ascii (i.e. >0xa0 chars)
        # force all strings to be str and you're good, though. hence stuff above
        # s = ''
        # for f in flattened:
        #     logging.debug("part("+str(type(f))+"): " + f[:32])
        #     s += f
        #     s += '\r\n'
        # return s[:-2]
        return '\r\n'.join(flattened)


if __name__ == '__main__':
    # Create the form with simple fields
    form = MultiPartForm()
    form.add_field('firstname', 'Doug')
    form.add_field('lastname', 'Hellmann')

    # Add a fake file
    form.add_file('biography', 'bio.txt', 
                  fileHandle=StringIO('Python developer and blogger.'))

    # Build the request
    request = urllib2.Request('http://localhost:8080/')
    request.add_header('User-agent', 'PyMOTW (http://www.doughellmann.com/PyMOTW/)')
    body = str(form)
    request.add_header('Content-type', form.get_content_type())
    request.add_header('Content-length', len(body))
    request.add_data(body)

    print
    print 'OUTGOING DATA:'
    print request.get_data()

    print
    print 'SERVER RESPONSE:'
    print urllib2.urlopen(request).read()
