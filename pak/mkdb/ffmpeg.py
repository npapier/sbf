#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for clx.y
descriptor = {
 'urls'			: ['http://ffmpeg.arrozcru.org/builds/shared/ffmpeg-r16537-gpl-lshared-win32.tar.bz2'],

 'name'			: 'ffmpeg',
 'version'		: '16537',

 'license'		: ['GPL.txt'],
 'include'		: ['include/'],
 'lib'			: ['bin/*.dll', 'lib/*.lib']
}
