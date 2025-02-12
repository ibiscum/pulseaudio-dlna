#!/usr/bin/python
# -*- coding: utf-8 -*-

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

import requests
import logging
import sys
import concurrent.futures

import pulseaudio_dlna
import pulseaudio_dlna.holder
import pulseaudio_dlna.plugins.dlna
import pulseaudio_dlna.plugins.chromecast
import pulseaudio_dlna.codecs

level = logging.INFO
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

logging.basicConfig(
    level=level,
    format='%(asctime)s %(name)-46s %(levelname)-8s %(message)s',
    datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger('radio')


class RadioLauncher:
    PLUGINS = [
        pulseaudio_dlna.plugins.dlna.DLNAPlugin(),
        pulseaudio_dlna.plugins.chromecast.ChromecastPlugin(),
    ]

    def __init__(self, max_workers=10):
        self.devices = self._discover_devices()
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers)

    def stop(self, _name, _flavour=None):
        self.thread_pool.submit(self._stop, _name, _flavour)

    def _stop(self, _name, _flavour=None):
        _device = self._get_device(_name, _flavour)
        if _device:
            return_code, message = _device.stop()
            if return_code == 200:
                logger.info(
                    'The device "{name}" was instructed to stop'.format(
                        name=_device.label))
            else:
                logger.info(
                    'The device "{name}" failed to stop ({code})'.format(
                        name=_device.label, code=return_code))

    def play(self, url, _name, _flavour=None,
             artist=None, title=None, thumb=None):
        self.thread_pool.submit(
            self._play, url, _name, _flavour, artist, title, thumb)

    def _play(self, url, _name, _flavour=None,
              artist=None, title=None, thumb=None):
        if url.lower().endswith('.m3u'):
            url = self._get_playlist_url(url)
        codec = self._get_codec(url)
        _device = self._get_device(_name, _flavour)
        if _device:
            return_code, message = _device.play(url, codec, artist, title, thumb)
            if return_code == 200:
                logger.info(
                    'The device "{name}" was instructed to play'.format(
                        name=_device.label))
            else:
                logger.info(
                    'The device "{name}" failed to play ({code})'.format(
                        name=_device.label, code=return_code))

    def _get_device(self, _name, _flavour=None):
        for _device in self.devices:
            if _flavour:
                if _device.name == _name and _device.flavour == _flavour:
                    return _device
            else:
                if _device.name == _name:
                    return _device
        return None

    @staticmethod
    def _get_codec(url):
        for identifier, _type in pulseaudio_dlna.codecs.CODECS.items():
            codec = _type()
            if url.endswith(codec.suffix):
                return codec
        return pulseaudio_dlna.codecs.Mp3Codec()

    @staticmethod
    def _get_playlist_url(url):
        response = requests.get(url=url)
        for line in response.content.split('\n'):
            if line.lower().startswith('http://'):
                return line
        return None

    def _discover_devices(self):
        holder = pulseaudio_dlna.holder.Holder(self.PLUGINS)
        holder.search(ttl=5)
        logger.info('Found the following devices:')
        for udn, _device in holder.devices.items():
            logger.info('  - "{name}" ({flavour})'.format(
                name=_device.name, flavour=_device.flavour))
        return holder.devices.values()


# Local pulseaudio-dlna installations running in a virutalenv should run this
#   script as module:
#     python -m scripts/radio [--list | --stop]

args = sys.argv[1:]
rl = RadioLauncher()

if len(args) > 0 and args[0] == '--list':
    sys.exit(0)

devices = [
    ('Alle', 'Chromecast'),
]

for device in devices:
    name, flavour = device
    if len(args) > 0 and args[0] == '--stop':
        rl.stop(name, flavour)
    else:
        rl.play(
            'http://www.wdr.de/wdrlive/media/einslive.m3u', name, flavour,
            'Radio', 'Einslive',
            'https://lh4.ggpht.com/7ssDAyz52UL1ahViwMkCrtfbdj45RU1Gqqpw3ncYjMrjhZofECX01j4nBufhCAkRFtRm=w600')
