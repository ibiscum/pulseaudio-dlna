#!/usr/bin/python

# This file is part of pulseaudio-dlna.

# pulseaudio-dlna is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# pulseaudio-dlna is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with pulseaudio-dlna.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import logging
import sys
import locale
import chardet

logger = logging.getLogger('pulseaudio_dlna.plugins.utils.encoding')


class NotBytesException(Exception):
    def __init__(self, var):
        Exception.__init__(
            self,
            'The specified variable is {}". '
            'Must be bytes.'.format(type(var))
        )


def decode_default(_bytes):
    if type(_bytes) is not str:
        raise NotBytesException(_bytes)
    guess = chardet.detect(_bytes)
    encodings = {
        'sys.stdout.encoding': sys.stdout.encoding,
        'locale.getpreferredencoding': locale.getpreferredencoding(),
        'chardet.detect': guess['encoding'],
        'utf-8': 'utf-8',
        'latin1': 'latin1',
    }
    for encoding in encodings.values():
        if encoding and encoding != 'ascii':
            try:
                return _bytes.decode(encoding)
            except UnicodeDecodeError:
                continue
    try:
        return _bytes.decode('ascii', errors='replace')
    except UnicodeDecodeError:
        logger.error(
            'Decoding failed using the following encodings: "{}"'.format(
                ','.join(
                    ['{}:{}'.format(f, e) for f, e in encodings.items()]
                )))
        return 'Unknown'


def _bytes2hex(_bytes, seperator=':'):
    if type(_bytes) is not str:
        raise NotBytesException(_bytes)
    return seperator.join('{:02x}'.format(ord(b)) for b in _bytes)


def _hex2bytes(_hex, seperator=':'):
    return b''.join(chr(int(h, 16)) for h in _hex.split(seperator))
