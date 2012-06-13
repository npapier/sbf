#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2011, 2012, Nicolas Papier.
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

popplerRootBuildDir = '{0}-{1}'.format( descriptorName, descriptorVersionDot )
absRootBuildDir = os.path.join( buildDirectory, descriptorName + descriptorVersion )

if CCVersionNumber in [8, 9, 10, 11]:

	options =  ' -D FREETYPE_INCLUDE_DIR_freetype2="{0}/include/freetype2" -D FREETYPE_INCLUDE_DIR_ft2build="{0}/include" -D FREETYPE_LIBRARY="{0}/lib/freetype.lib" '.format( absRootBuildDir )

	options += ' -D ENABLE_ZLIB=ON -D ZLIB_INCLUDE_DIR="{0}/include" -D ZLIB_LIBRARY="{0}/lib/zdll.lib" '.format( absRootBuildDir )

	options += ' -D PNG_PNG_INCLUDE_DIR="{0}/include" -D PNG_LIBRARY="{0}/lib/libpng.lib" '.format( absRootBuildDir )

	options += ' -D ICONV_INCLUDE_DIR="{0}/include" -D ICONV_LIBRARIES="{0}/lib/libiconv.lib" '.format( absRootBuildDir )

	options += ' -D JPEG_INCLUDE_DIR="{0}/include" -D JPEG_LIBRARY="{0}/lib/jpeg.lib" '.format( absRootBuildDir )

	options += ' -D WITH_Qt4=OFF '

#	options += ' -D CMAKE_DEBUG_POSTFIX="-d" -D BUILD_SHARED_LIBS=ON '
	options += ' -D CMAKE_DEBUG_POSTFIX="-d" -D CMAKE_SHARED_LINKER_FLAGS_RELEASE=" /INCREMENTAL:YES" '
else:
	print >>sys.stderr, "Wrong MSVC version. Version 8.0[Exp], 9.0[Exp], 10.0[Exp] or 11.0[Exp] required."
	exit(1)

descriptor = {

	'urls':		[
# dependencies embedded in gtkmm
#freetype2 version 2.4.2, zlib version 1.2.5 and libpng version 1.4.3 in gtkmm 2.22.0-2
					'http://ftp.gnome.org/pub/gnome/binaries/win32/dependencies/freetype_2.4.2-1_win32.zip',
					'http://ftp.gnome.org/pub/gnome/binaries/win32/dependencies/freetype-dev_2.4.2-1_win32.zip',
					'http://ftp.gnome.org/pub/gnome/binaries/win32/dependencies/freetype-2.4.2.tar.bz2',

					'http://ftp.gnome.org/pub/gnome/binaries/win32/dependencies/zlib_1.2.5-2_win32.zip',
					'http://ftp.gnome.org/pub/gnome/binaries/win32/dependencies/zlib-dev_1.2.5-2_win32.zip',
					'http://www.zlib.net/zlib125.zip',

					'http://ftp.gnome.org/pub/gnome/binaries/win32/dependencies/libpng_1.4.3-1_win32.zip',
					'http://ftp.gnome.org/pub/gnome/binaries/win32/dependencies/libpng-dev_1.4.3-1_win32.zip',
					'ftp://ftp.simplesystems.org/pub/png/src/history/libpng-1.4.3.tar.bz2',

# dependencies to embedded
					'http://freefr.dl.sourceforge.net/project/gnuwin32/jpeg/6b-4/jpeg-6b-4-lib.zip',
					'http://freefr.dl.sourceforge.net/project/gnuwin32/jpeg/6b-4/jpeg-6b-4-bin.zip',
					'http://freefr.dl.sourceforge.net/project/gnuwin32/jpeg/6b-4/jpeg-6b-4-dep.zip',
					'http://freefr.dl.sourceforge.net/project/gnuwin32/jpeg/6b-4/jpeg-6b-4-src.zip',

					'http://freefr.dl.sourceforge.net/project/gnuwin32/libiconv/1.9.2-1/libiconv-1.9.2-1-lib.zip',
					'http://freefr.dl.sourceforge.net/project/gnuwin32/libiconv/1.9.2-1/libiconv-1.9.2-1-bin.zip',
					'http://freefr.dl.sourceforge.net/project/gnuwin32/libiconv/1.9.2-1/libiconv-1.9.2-1-dep.zip',
					'http://freefr.dl.sourceforge.net/project/gnuwin32/libiconv/1.9.2-1/libiconv-1.9.2-1-src.zip',

					'http://poppler.freedesktop.org/poppler-{0}.tar.gz'.format( descriptorVersionDot ) ],

	'name'		:	descriptorName,
	'version'	:	descriptorVersion,

	'rootBuildDir'	: popplerRootBuildDir,
	'builds'		: [ getCMakeCmdConfigure(CCVersionNumber, options), getCMakeCmdBuildDebug(), getCMakeCmdBuildRelease() ],


	'rootDir'		: popplerRootBuildDir,

	'include'		: [	'cpp/*.h' ],

	'lib'			:	[	# poppler
							'Debug/*.pdb', 'Debug/*.lib',
							'Release/*.lib',
							# poppler-cpp
							'cpp/Debug/*.dll', 'cpp/Debug/*.pdb', 'cpp/Debug/*.lib',
							'cpp/Release/*.dll', 'cpp/Release/*.lib',
							# jpeg
							'../bin/jpeg62.dll', '../bin/librle3.dll',
							# libiconv
							'../bin/libcharset1.dll', '../bin/libiconv2.dll', '../bin/libintl3.dll',
							],

	'license'		:	[	'COPYING', '../src/jpeg/6b/jpeg-6b-src/README', '../src/libiconv/1.9.2/libiconv-1.9.2-src/README' ]
}
