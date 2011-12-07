#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2010, 2011, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier
# Author Maxime Peresson

# http://icculus.org/physfs/
# cl8-0[Exp], cl9-0[Exp], cl10-0[Exp] and cl11-0[Exp]
# Support for zip (zlib123), 7z (using lzma)

import os.path

descriptorName = 'physfs'
descriptorVersion = '2-0-2'
descriptorVersionWithDot = descriptorVersion.replace('-', '.')

cmakeGenerator = {
	8	: 'Visual Studio 8 2005',
	9	: 'Visual Studio 9 2008',
	10	: 'Visual Studio 10',
	11	: 'Visual Studio 11' }

if CCVersionNumber in [8, 9, 10, 11]:
	options = '-D PHYSFS_ARCHIVE_GRP:BOOL=OFF -D PHYSFS_ARCHIVE_HOG:BOOL=OFF -D PHYSFS_ARCHIVE_MVL:BOOL=OFF -D PHYSFS_ARCHIVE_QPAK:BOOL=OFF -D PHYSFS_ARCHIVE_WAD:BOOL=OFF -D PHYSFS_BUILD_STATIC:BOOL=OFF'
	cmdConfigure = 'cmake -G "{generator}" {options} CMakeLists.txt'.format( generator=cmakeGenerator[CCVersionNumber], options=options )
	# @todo generates debug version with a different name
	#cmdDebug = 'cmake --build . --config debug'
	cmdRelease = 'cmake --build . --config release'
else:
	print >>sys.stderr, "Wrong MSVC version. Version 8.0[Exp], 9.0[Exp], 10.0[Exp] or 11.0[Exp] required."
	exit(1)

descriptor = {
 'urls'			: [ 'http://icculus.org/physfs/downloads/physfs-2.0.2.tar.gz' ],

 'rootBuildDir'	: descriptorName + '-' + descriptorVersionWithDot,
 #'builds'		: [ cmdConfigure, cmdDebug, cmdRelease ],
 'builds'		: [ cmdConfigure, cmdRelease ],

 'name'			: descriptorName,
 'version'		: descriptorVersion,

 'rootDir'		: descriptorName + '-' + descriptorVersionWithDot,
 
 'license'		: [('LICENSE.txt'), ('CREDITS.txt'), ('lzma/lzma.txt'), ('zlib123/README')],

 'include'		: [	'*.h' ],

 'lib'			: [	'Release/physfs.lib',
					'Release/physfs.dll' ]
}
