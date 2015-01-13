#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2010, 2011, 2013, 2014, 2015, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier
# Author Maxime Peresson

# http://icculus.org/physfs/

# cl8-0[Exp], cl9-0[Exp], cl10-0[Exp], cl11-0[Exp] and cl12-0[Exp] (32/64bits), emcc and gcc
# Support for zip (zlib123), 7z (using lzma)

import os.path

descriptorName = 'physfs'
descriptorVersion = '2-0-2'
descriptorVersionWithDot = descriptorVersion.replace('-', '.')

from src.sbfCMake import getCMakeCmdConfigure, getCMakeCmdBuildDebug, getCMakeCmdBuildRelease

RequiredProgram('cmake')

# @todo -DPHYSFS_HAVE_CDROM_SUPPORT:BOOL=OFF
options = ' -D PHYSFS_ARCHIVE_GRP:BOOL=OFF -D PHYSFS_ARCHIVE_HOG:BOOL=OFF -D PHYSFS_ARCHIVE_MVL:BOOL=OFF -D PHYSFS_ARCHIVE_QPAK:BOOL=OFF -D PHYSFS_ARCHIVE_WAD:BOOL=OFF -D PHYSFS_BUILD_TEST=OFF '
options += ' -D CMAKE_DEBUG_POSTFIX=-d '

if platform == 'win':
	if CC == 'cl':
		options += ' -D PHYSFS_BUILD_STATIC=OFF -DPHYSFS_BUILD_SHARED=ON '
		cmdConfigure = getCMakeCmdConfigure(CC, CCVersionNumber, arch, options)
		builds = [ cmdConfigure, getCMakeCmdBuildDebug(), getCMakeCmdBuildRelease() ]
		lib = ['debug/physfs-d.lib ', 'release/physfs.lib']
		binR = ['release/physfs.dll']
		binD = ['debug/physfs-d.dll']
	elif CC == 'emcc':
		options += ' -D PHYSFS_BUILD_STATIC=ON -DPHYSFS_BUILD_SHARED=OFF '
		cmdConfigure = getCMakeCmdConfigure(CC, CCVersionNumber, arch, options)
		builds = [	cmdConfigure, getCMakeCmdBuildRelease() ] # @todo getCMakeCmdBuildDebug(),
		lib = ['libphysfs.a'] # @todo 'libphysfs-d.a'
		binR = []
		binD = []
else:
	lib = []
	binR = ['*.so.*']
	binD = []



descriptor = {
 'urls'			: [ 'http://icculus.org/physfs/downloads/physfs-2.0.2.tar.gz' ],

 'rootBuildDir'	: descriptorName + '-' + descriptorVersionWithDot,
 'builds'		: builds,

 'name'			: descriptorName,
 'version'		: descriptorVersion,

 # packages developer and runtime
 'rootDir'		: descriptorName + '-' + descriptorVersionWithDot,

 # developer package
 'license'		: [('LICENSE.txt'), ('CREDITS.txt'), ('lzma/lzma.txt'), ('zlib123/README')],
 'include'		: [	'*.h' ],
 'lib'			: lib,

 # runtime package (release version)
 'binR'			: binR,
 
 # runtime package (debug version)
 'binD'			: binD,
}
