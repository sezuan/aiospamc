#!/usr/bin/env python3

'''Contains classes used for responses.'''

import enum
import re

from aiospamc.common import RequestResponseBase
from aiospamc.exceptions import (BadResponse,
                                 UsageException, DataErrorException, NoInputException, NoUserException,
                                 NoHostException, UnavailableException, InternalSoftwareException, OSErrorException,
                                 OSFileException, CantCreateException, IOErrorException, TemporaryFailureException,
                                 ProtocolException, NoPermissionException, ConfigException, TimeoutException)


class Status(enum.IntEnum):
    '''Enumeration of status codes that the SPAMD will accompany with a
    response.

    Reference: https://svn.apache.org/repos/asf/spamassassin/trunk/spamd/spamd.raw
    Look for the %resphash variable.
    '''

    #pylint: disable=C0326
    def __new__(cls, value, exception=None, description=''):
        #pylint: disable=protected-access
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.exception = exception
        obj.description = description

        return obj

    EX_OK           = 0,    None,          'No problems'
    EX_USAGE        = 64, UsageException, 'Command line usage error'
    EX_DATAERR      = 65, DataErrorException, 'Data format error'
    EX_NOINPUT      = 66, NoInputException, 'Cannot open input'
    EX_NOUSER       = 67, NoUserException, 'Addressee unknown'
    EX_NOHOST       = 68, NoHostException, 'Host name unknown'
    EX_UNAVAILABLE  = 69, UnavailableException, 'Service unavailable'
    EX_SOFTWARE     = 70, InternalSoftwareException, 'Internal software error'
    EX_OSERR        = 71, OSErrorException, 'System error (e.g., can\'t fork)'
    EX_OSFILE       = 72, OSFileException, 'Critical OS file missing'
    EX_CANTCREAT    = 73, CantCreateException, 'Can\'t create (user) output file'
    EX_IOERR        = 74, IOErrorException, 'Input/output error'
    EX_TEMPFAIL     = 75, TemporaryFailureException, 'Temp failure; user is invited to retry'
    EX_PROTOCOL     = 76, ProtocolException, 'Remote error in protocol'
    EX_NOPERM       = 77, NoPermissionException, 'Permission denied'
    EX_CONFIG       = 78, ConfigException, 'Configuration error'
    EX_TIMEOUT      = 79, TimeoutException, 'Read timeout'

class Response(RequestResponseBase):
    '''Class to encapsulate response.

    Attributes
    ----------
    protocol_version : str
        Protocol version given by the response.
    status_code : aiospamc.responess.Status
        Status code give by the response.
    message : str
        Message accompanying the status code.
    body : str
        Contents of the response body.
    '''

    #pylint: disable=too-few-public-methods
    _response_pattern = re.compile(r'^\s*'
                                   r'(?P<protocol>SPAMD)/(?P<version>\d+\.\d+)'
                                   r'\s+'
                                   r'(?P<status>\d+)'
                                   r'\s+'
                                   r'(?P<message>.*)')
    '''Regular expression pattern to match the response.  Protocol will match
    the phrase 'SPAMD', version will match with the style '1.0', status will
    match an integer.  The message will match all characters up until the next
    newline.
    '''
    _response_string = 'SPAMD/{version} {status} {message}\r\n{headers}\r\n{body}'
    '''String used for composing a response.'''

    @classmethod
    def parse(cls, response):
        response, *body = response.split(b'\r\n\r\n', 1)
        response, *headers = response.split(b'\r\n')

        response = response.decode()

        # Process response
        match = cls._response_pattern.match(response)
        if match:
            response_match = match.groupdict()
        else:
            # Not a SPAMD response
            raise BadResponse

        protocol_version = response_match['version'].strip()
        status_code = Status(int(response_match['status']))
        message = response_match['message'].strip()

        if status_code.exception:
            raise status_code.exception(message)

        parsed_headers = cls._parse_headers(headers)
        parsed_body = cls._parse_body(body[0] if body else None, parsed_headers)

        obj = cls(protocol_version,
                  status_code,
                  message,
                  parsed_body,
                  *parsed_headers)

        return obj

    def __init__(self, protocol_version, status_code, message, body=None, *headers):
        '''Response constructor.

        Parameters
        ----------
        protocol_version : str
            Version reported by the SPAMD service response.
        status_code : aiospamc.responses.Status
            Success or error code.
        message : str
            Message associated with status code.
        body : :obj:`str`, optional
            String representation of the body.  An instance of the
            aiospamc.headers.ContentLength will be automatically added.
        *headers : :obj:`aiospamc.headers.Header`, optional
            Collection of headers to be added.  If it contains an instance of
            aiospamc.headers.Compress then the body is automatically
            compressed.
        '''

        self.protocol_version = protocol_version
        self.status_code = status_code
        self.message = message
        super().__init__(body, *headers)

    def __bytes__(self):
        if self._compressed_body:
            body = self._compressed_body
        elif self.body:
            body = self.body.encode()
        else:
            body = b''

        return (b'SPAMD/%(version)b '
                b'%(status)d '
                b'%(message)b\r\n'
                b'%(headers)b\r\n'
                b'%(body)b') % {b'version': b'1.5',
                                b'status': self.status_code.value,
                                b'message': self.message.encode(),
                                b'headers': b''.join(map(bytes, self._headers.values())),
                                b'body': body}

    def __repr__(self):
        resp_format = ('{}(protocol_version={}, '
                       'status_code={}, '
                       'message={}, '
                       'headers={}, '
                       'body={})')

        return resp_format.format(self.__class__.__name__,
                                  repr(self.protocol_version),
                                  str(self.status_code),
                                  repr(self.message),
                                  tuple(self._headers.values()),
                                  repr(self.body) if self.body else 'None')
