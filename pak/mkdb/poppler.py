#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2011, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Guillaume Brocker

descriptor = {

	'urls':		[	'http://sourceforge.net/projects/gnuwin32/files/jpeg/6b-4/jpeg-6b-4-bin.zip',
					'http://sourceforge.net/projects/gnuwin32/files/jpeg/6b-4/jpeg-6b-4-dep.zip',
					'http://freefr.dl.sourceforge.net/project/gnuwin32/jpeg/6b-4/jpeg-6b-4-src.zip',
					
					'http://freefr.dl.sourceforge.net/project/gnuwin32/freetype/2.3.5-1/freetype-2.3.5-1-bin.zip',
					'http://freefr.dl.sourceforge.net/project/gnuwin32/freetype/2.3.5-1/freetype-2.3.5-1-dep.zip',
					'http://freefr.dl.sourceforge.net/project/gnuwin32/freetype/2.3.5-1/freetype-2.3.5-1-src.zip',
					
					'http://freefr.dl.sourceforge.net/project/gnuwin32/libiconv/1.9.2-1/libiconv-1.9.2-1-bin.zip',
					'http://freefr.dl.sourceforge.net/project/gnuwin32/libiconv/1.9.2-1/libiconv-1.9.2-1-dep.zip',
					'http://freefr.dl.sourceforge.net/project/gnuwin32/libiconv/1.9.2-1/libiconv-1.9.2-1-src.zip',

					'http://orange/files/Dev/localExt/src/poppler-0.16.5-dev.zip',
					'http://poppler.freedesktop.org/poppler-0.16.5.tar.gz' ],
	
	'name':		'poppler',
	'version':	'0-16-5',
	
	'include':	[	'include/poppler/cpp/*' ],
	
	'lib':		[	'bin/jpeg62.dll', 'bin/librle3.dll',							# jpeg
					'bin/freetype6.dll', 											# fretype
					'bin/libcharset1.dll', 'bin/libiconv2.dll',	'bin/libintl3.dll',	# libiconv
					'bin/poppler*', 'lib/poppler*' ],								# poppler
					
	'custom':	[	('poppler-0.16.5/COPYING','license/license.poppler0-16-5.txt'),
					('src/jpeg/6b/jpeg-6b-src/README','license/license.jpeg6b.txt'),
					('src/freetype/2.3.5/freetype-2.3.5/docs/LICENSE.TXT','license/license.freetype2-3-5.txt'),
					('src/libiconv/1.9.2/libiconv-1.9.2-src/COPYING.LIB','license/license.libiconv1-9-2.txt') ]
}
