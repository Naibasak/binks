# coding=utf-8

import os
import time
import posixpath
import urllib
import mimetypes

class FileRoutingMiddleware:
    def translate_path(self, path):
	    """Translate a /-separated PATH to the local filename syntax.

	    Components that mean special things to the local file system
	    (e.g. drive or directory names) are ignored.  (XXX They should
	    probably be diagnosed.)

	    """
	    # abandon query parameters
	    path = path.split('?',1)[0]
	    path = path.split('#',1)[0]

	    path = posixpath.normpath(urllib.unquote(path))
	    words = path.split('/')
	    words = filter(None, words)

	    path = os.getcwd()
	    for word in words:
	        drive, word = os.path.splitdrive(word)
	        head, word = os.path.split(word)

	        if word in (os.curdir, os.pardir): continue
	        path = os.path.join(path, word)
	    return path

    def date_time_string(self, timestamp=None):
        """Return the current date and time formatted for a message header."""
        if timestamp is None:
            timestamp = time.time()
        year, month, day, hh, mm, ss, wd, y, z = time.gmtime(timestamp)
        s = "%s, %02d %3s %4d %02d:%02d:%02d GMT" % (
                self.weekdayname[wd],
                day, self.monthname[month], year,
                hh, mm, ss)
        return s

    def guess_type(self, ext):
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']

    def readfile(self, path):
    	path = self.translate_path(path)
        base, ext = posixpath.splitext(path)
    	ctype = self.guess_type(ext)

    	if ext in self.ignore_ext_map:
    		return None,None

    	f = None
    	try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
            fs = os.fstat(f.fileno())
            buf = f.read(-1)
            f.close()
            return buf,[("Content-type", ctype), ("Last-Modified", self.date_time_string(fs.st_mtime))]
        except IOError:
            if f is not None:
                f.close()
            return None,None

    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream', # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
        })

    ignore_ext_map = (".pyc", ".py", ".log", ".sh", ".bat", ".xls", ".csv", ".zip", ".gz", ".out", ".doc", ".docx")
    weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    monthname = [None,
                 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

frmw = FileRoutingMiddleware()