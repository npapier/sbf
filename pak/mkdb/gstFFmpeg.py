#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, 2010, 2013, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# FFmpeg LGPL version from GStreamer

# http://code.google.com/p/ossbuild/

# Remarks : DEAD PROJECT => MOVE to VLC (now LGPL)

# ok for cl x.y
descriptor = {
 'urls'			: ['http://orange/files/Dev/localExt/src/GStreamer-WinBuilds-SDK-LGPL-x86-v0.10.6.zip'],
 'svnUrl'		: 'http://msinttypes.googlecode.com/svn/trunk@29',
# patch to stdint.h from msinttypes in r29
#// 7.18.4.2 Macros for greatest-width integer constants
#ifndef INTMAX_C //   [
#	define INTMAX_C   INT64_C
#endif // INTMAX_C    ]
#ifndef UINTMAX_C //  [
#	define UINTMAX_C  UINT64_C
#endif // UINTMAX_C   ]
 'name'			: 'gstFFmpeg',
 'version'		: '0-10-9',

 'rootDir'		: 'GStreamer-WinBuilds-SDK-LGPL-x86-v0.10.6/GStreamer/v0.10.6',

 # developer package
 'license'		: ['share/licenses/ffmpeg.txt'],
 'include'		: [	'../../../gstFFmpeg/inttypes.h', # '../../../gstFFmpeg/stdint.h', conflict with boost/cstdint.h (cl == 11)

					('sdk/include/libavcodec/',		'libavcodec/'),
					('sdk/include/libavdevice/',	'libavdevice/'),
					('sdk/include/libavfilter/',	'libavfilter/'),
					('sdk/include/libavformat/',	'libavformat/'),
					('sdk/include/libavutil/',		'libavutil/'),
					('sdk/include/libswscale/',		'libswscale/') ],

 'lib'			: [	'sdk/lib/avcodec-lgpl.lib',
					'sdk/lib/avdevice-lgpl.lib',
					'sdk/lib/avfilter-lgpl.lib',
					'sdk/lib/avformat-lgpl.lib',
					'sdk/lib/avutil-lgpl.lib',
					'sdk/lib/swscale-lgpl.lib' ],

 # runtime package
 'bin'			: [	'bin/avcodec-lgpl-52.dll',
					'bin/avdevice-lgpl-52.dll',
					'bin/avfilter-lgpl-1.dll',
					'bin/avformat-lgpl-52.dll',
					'bin/avutil-lgpl-50.dll',
					'bin/swscale-lgpl-0.dll',

					'bin/z.dll', 'bin/libbz2.dll' ]
}
