#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2010, 2011, 2013, Nicolas Papier.
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

from src.sbfCMake import getCMakeCmdConfigure, getCMakeCmdBuildDebug, getCMakeCmdBuildRelease

options = '-D PHYSFS_ARCHIVE_GRP:BOOL=OFF -D PHYSFS_ARCHIVE_HOG:BOOL=OFF -D PHYSFS_ARCHIVE_MVL:BOOL=OFF -D PHYSFS_ARCHIVE_QPAK:BOOL=OFF -D PHYSFS_ARCHIVE_WAD:BOOL=OFF -D PHYSFS_BUILD_STATIC:BOOL=OFF'
options += ' -D CMAKE_DEBUG_POSTFIX=-d '
cmdConfigure = getCMakeCmdConfigure(CCVersionNumber, options)

descriptor = {
 'urls'			: [ 'http://icculus.org/physfs/downloads/physfs-2.0.2.tar.gz' ],

 'rootBuildDir'	: descriptorName + '-' + descriptorVersionWithDot,
 'builds'		: [ cmdConfigure, getCMakeCmdBuildDebug(), getCMakeCmdBuildRelease() ],

 'name'			: descriptorName,
 'version'		: descriptorVersion,

 # packages developer and runtime
 'rootDir'		: descriptorName + '-' + descriptorVersionWithDot,

 # developer package
 'license'		: [('LICENSE.txt'), ('CREDITS.txt'), ('lzma/lzma.txt'), ('zlib123/README')],
 'include'		: [	'*.h' ],
 'lib'			: [	'debug/physfs-d.lib ', 'release/physfs.lib' ],

 # runtime package (release version)
 'binR'			: ['release/physfs.dll'],
 
 # runtime package (debug version)
 'binD'			: ['debug/physfs-d.dll'],
 }
