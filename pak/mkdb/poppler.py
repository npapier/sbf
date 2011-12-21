#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2011, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Guillaume Brocker
# Author Nicolas Papier

# cl8, 9, 10, 11 [Exp]

descriptorName = 'poppler'
descriptorVersion = '0-16-5'
descriptorVersionDot = descriptorVersion.replace('-', '.')

import os.path

from src.sbfCMake import getCMakeCmdConfigure, getCMakeCmdBuildDebug, getCMakeCmdBuildRelease
from src.sbfUtils import getPathFromEnv

# Retrieves GTKMM_BASEPATH
GTKMM_BASEPATH = getPathFromEnv('GTKMM_BASEPATH')

popplerRootBuildDir = '{0}-{1}'.format( descriptorName, descriptorVersionDot )
absRootBuildDir = os.path.join( buildDirectory, descriptorName + descriptorVersion )

if CCVersionNumber in [8, 9, 10, 11]:
	options = ' -D FREETYPE_INCLUDE_DIR_freetype2="{0}/include/freetype2" -D FREETYPE_INCLUDE_DIR_ft2build="{0}/include" -D FREETYPE_LIBRARY="{0}/lib/freetype.lib" '.format( absRootBuildDir )
	options += ' -D ICONV_INCLUDE_DIR="{0}/include" -D ICONV_LIBRARIES="{0}/lib/libiconv.lib" '.format( absRootBuildDir )
	options += ' -D JPEG_INCLUDE_DIR="{0}/include" -D JPEG_LIBRARY="{0}/lib/jpeg.lib" '.format( absRootBuildDir )
	options += ' -D CMAKE_DEBUG_POSTFIX=-d -D BUILD_SHARED_LIBS:BOOL=ON '
	options += ' -D ENABLE_ZLIB=ON -D ZLIB_INCLUDE_DIR="{0}/include" -D ZLIB_LIBRARY="{0}/lib/zdll.lib" '.format( GTKMM_BASEPATH )
	options += ' -D PNG_PNG_INCLUDE_DIR="{0}>/include/libpng14" -D PNG_LIBRARY="{0}/lib/libpng.lib" '.format( GTKMM_BASEPATH )
else:
	print >>sys.stderr, "Wrong MSVC version. Version 8.0[Exp], 9.0[Exp], 10.0[Exp] or 11.0[Exp] required."
	exit(1)

descriptor = {

	'urls':		[
					'http://freefr.dl.sourceforge.net/project/gnuwin32/freetype/2.3.5-1/freetype-2.3.5-1-lib.zip',
					'http://freefr.dl.sourceforge.net/project/gnuwin32/freetype/2.3.5-1/freetype-2.3.5-1-bin.zip',
					'http://freefr.dl.sourceforge.net/project/gnuwin32/freetype/2.3.5-1/freetype-2.3.5-1-dep.zip',
					'http://freefr.dl.sourceforge.net/project/gnuwin32/freetype/2.3.5-1/freetype-2.3.5-1-src.zip',

					'http://freefr.dl.sourceforge.net/project/gnuwin32/libiconv/1.9.2-1/libiconv-1.9.2-1-lib.zip',
					'http://freefr.dl.sourceforge.net/project/gnuwin32/libiconv/1.9.2-1/libiconv-1.9.2-1-bin.zip',
					'http://freefr.dl.sourceforge.net/project/gnuwin32/libiconv/1.9.2-1/libiconv-1.9.2-1-dep.zip',
					'http://freefr.dl.sourceforge.net/project/gnuwin32/libiconv/1.9.2-1/libiconv-1.9.2-1-src.zip',

					'http://freefr.dl.sourceforge.net/project/gnuwin32/jpeg/6b-4/jpeg-6b-4-lib.zip',
					'http://freefr.dl.sourceforge.net/project/gnuwin32/jpeg/6b-4/jpeg-6b-4-bin.zip',
					'http://freefr.dl.sourceforge.net/project/gnuwin32/jpeg/6b-4/jpeg-6b-4-dep.zip',
					'http://freefr.dl.sourceforge.net/project/gnuwin32/jpeg/6b-4/jpeg-6b-4-src.zip',

					'http://poppler.freedesktop.org/poppler-{0}.tar.gz'.format( descriptorVersionDot ) ],

	'name':		descriptorName,
	'version':	descriptorVersion,

	'rootBuildDir'	: popplerRootBuildDir,
	'builds'		: [ getCMakeCmdConfigure(CCVersionNumber, options), getCMakeCmdBuildDebug(), getCMakeCmdBuildRelease() ],


	'rootDir'		: popplerRootBuildDir,

	'include'		: [	'cpp/*.h' ],

	'lib'			:	[	'../bin/jpeg62.dll', '../bin/librle3.dll',									# jpeg
						'../bin/freetype6.dll', 														# fretype
						'../bin/libcharset1.dll', '../bin/libiconv2.dll', '../bin/libintl3.dll',		# libiconv
						# poppler
						'Debug/*.pdb', 'Debug/*.lib',
						'cpp/Debug/*.dll', 'cpp/Debug/*.pdb', 'cpp/Debug/*.lib',
						'Release/*.lib',
						'cpp/Release/*.dll', 'cpp/Release/*.lib' ],

	'license'		:	[	'COPYING', '../src/jpeg/6b/jpeg-6b-src/README',
							'../src/freetype/2.3.5/freetype-2.3.5/docs/LICENSE.TXT', '../src/libiconv/1.9.2/libiconv-1.9.2-src/README' ]
}
