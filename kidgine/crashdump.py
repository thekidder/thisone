import datetime
import itertools
import logging
import mimetools
import mimetypes
import sys
import traceback
import urllib2

import utils


CRASH_URL='http://thekidder.com/effrafax/upload_crash/'

logger = logging.getLogger()


class CrashUploader(object):
    def __init__(self, version, log_name, diagnostics):
        self.version = version
        self.log_name = log_name
        self.diagnostics = diagnostics

        sys.excepthook = self.exception_handler


    def exception_handler(self, type, value, tb):
        logger.error('####################################')
        logger.error('Caught fatal error and will now exit')
        logger.error('####################################')

        self.diagnostics.dump_all()

        logger.error('Error: {}: {}\n{}'.format(type, value, ''.join(traceback.format_tb(tb))))

        utils.remove_file_logger()

        version = self.version
        date    = str(datetime.datetime.now())
        error   = '{}: {}'.format(type, value)
        file    = self.log_name

        form = MultiPartForm()
        form.add_field('crash_date', date)
        form.add_field('error', error)
        form.add_field('version', version)
        with open(file) as f:
            form.add_file('crash_file', file, f, 'text/plain')

        req = urllib2.Request(CRASH_URL)
        req.add_header('User-agent', version)

        body = str(form)
        req.add_header('Content-type', form.get_content_type())
        req.add_header('Content-length', len(body))
        req.add_data(body)

        try:
            urllib2.urlopen(req)
        except urllib2.URLError:
            logger.exception('Failed to upload crash dump')


class MultiPartForm(object):
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()
        return

    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))
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
              'Content-Disposition: file; name="%s"; filename="%s"' % \
                 (field_name, filename),
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
        return '\r\n'.join(flattened)
