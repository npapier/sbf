#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# FFmpeg LGPL version from GStreamer
# ok for clx.y
descriptor = {
 'urls'			: ['http://orange/files/Dev/localExt/src/GStreamer-WinBuilds-SDK-LGPL-x86-v0.10.6.zip'],
 'svnUrl'		: 'http://msinttypes.googlecode.com/svn/trunk/',

 'name'			: 'gstFFmpeg',
 'version'		: '0-10-9',

 'rootDir'		: 'GStreamer-WinBuilds-SDK-LGPL-x86-v0.10.6/GStreamer/v0.10.6',

 'license'		: ['share/licenses/ffmpeg.txt'],
 'include'		: [	'../../../gstFFmpeg/inttypes.h', '../../../gstFFmpeg/stdint.h',

					('sdk/include/libavcodec/',		'libavcodec/'),
					('sdk/include/libavdevice/',	'libavdevice/'),
					('sdk/include/libavfilter/',	'libavfilter/'),
					('sdk/include/libavformat/',	'libavformat/'),
					('sdk/include/libavutil/',		'libavutil/'),
					('sdk/include/libswscale/',		'libswscale/') ],
 'lib'			: [	'sdk/lib/avcodec-lgpl.lib',		'bin/avcodec-lgpl-52.dll',
					'sdk/lib/avdevice-lgpl.lib',	'bin/avdevice-lgpl-52.dll',
					'sdk/lib/avfilter-lgpl.lib',	'bin/avfilter-lgpl-1.dll',
					'sdk/lib/avformat-lgpl.lib',	'bin/avformat-lgpl-52.dll',
					'sdk/lib/avutil-lgpl.lib',		'bin/avutil-lgpl-50.dll',
					'sdk/lib/swscale-lgpl.lib',		'bin/swscale-lgpl-0.dll',

					'bin/z.dll', 'bin/libbz2.dll' ]
}
