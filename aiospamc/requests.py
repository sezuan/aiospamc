#!/usr/bin/env python3

import email.message
import zlib

from aiospamc.headers import *


class SpamdRequest:
    '''SPAMC request object.'''

    protocol = 'SPAMC/1.5'
    request_with_body = b'%(verb)b %(protocol)b\r\n%(headers)b\r\n%(body)b'
    request_without_body = b'%(verb)b %(protocol)b\r\n%(headers)b\r\n'

    def __init__(self, verb, body = None, headers = [], compress = False):
        ''''''

        self.verb = verb
        self.headers = headers
        self.body = body
        self.compress = compress

    def __bytes__(self):
        return self.compose()

    def __repr__(self):
        return 'SpamdRequest({}, {}, {})'.format(self.verb, self.headers, self.body)

    def compose(self):
        '''Composes a request based on the verb and headers that are currently set.'''

        if self.body:
            if self.compress:
                self.headers.append( Compress() )
                body_bytes = zlib.compress(bytes(self.body))
            else:
                body_bytes = bytes(self.body)
            self.headers.append( ContentLength( len(body_bytes) ) )
            request = self.request_with_body % { b'verb':     self.verb.encode(),
                                                 b'protocol': self.protocol.encode(),
                                                 b'headers':  b''.join(map(bytes, self.headers)),
                                                 b'body':     body_bytes }
        else:
            self.headers.append( ContentLength(0) )
            request = self.request_without_body % { b'verb':     self.verb.encode(),
                                                 b'protocol': self.protocol.encode(),
                                                 b'headers':  b''.join(map(bytes, self.headers)) }

        if self.body:
            self.headers.pop() # pop Content-length header
        if self.compress:
            self.headers.pop() # pop Compress header

        return request

class Check(SpamdRequest):
    def __init__(self, message, headers = [], compress = False):
        super().__init__('CHECK', message, headers, compress)

    def __repr__(self):
        return 'Check(message={}, headers={}, compress={})'.format(self.body, self.headers, self.compress)

class Headers(SpamdRequest):
    def __init__(self, message, headers = [], compress = False):
        super().__init__('HEADERS', message, headers, compress)

    def __repr__(self):
        return 'Headers(message={}, headers={}, compress={})'.format(self.body, self.headers, self.compress)

class Ping(SpamdRequest):
    def __init__(self, headers = []):
        super().__init__('PING', headers = headers)

    def __repr__(self):
        return 'Ping(headers={}, compress={})'.format(self.headers, self.compress)

class Process(SpamdRequest):
    def __init__(self, message, headers = [], compress = False):
        super().__init__('PROCESS', message, headers, compress)

    def __repr__(self):
        return 'Process(message={}, headers={}, compress={})'.format(self.body, self.headers, self.compress)

class Report(SpamdRequest):
    def __init__(self, message, headers = [], compress = False):
        super().__init__('REPORT', message, headers, compress)

    def __repr__(self):
        return 'Report(message={}, headers={}, compress={})'.format(self.body, self.headers, self.compress)

class ReportIfSpam(SpamdRequest):
    def __init__(self, message, headers = [], compress = False):
        super().__init__('REPORT_IFSPAM', message, headers, compress)

    def __repr__(self):
        return 'ReportIfSpam(message={}, headers={}, compress={})'.format(self.body, self.headers, self.compress)

class Symbols(SpamdRequest):
    def __init__(self, message, headers = [], compress = False):
        super().__init__('SYMBOLS', message, headers, compress)

    def __repr__(self):
        return 'Symbols(message={}, headers={}, compress={})'.format(self.body, self.headers, self.compress)

class Tell(SpamdRequest):
    def __init__(self, message, headers = [], compress = False):
        super().__init__('TELL', message, headers, compress)

    def __repr__(self):
        return 'Tell(message={}, headers={}, compress={})'.format(self.body, self.headers, self.compress)