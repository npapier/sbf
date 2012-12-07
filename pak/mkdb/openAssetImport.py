#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Guillaume Brocker
# Author Nicolas Papier

# cl8, 9, 10, 11, 12 [Exp]

descriptorName = 'openassetimport'
descriptorVersion = '3-0'
svnRevision = 1270
descriptorVersionDot = descriptorVersion.replace('-', '.')

import os.path

from src.sbfCMake import getCMakeCmdConfigure, getCMakeCmdBuildDebug, getCMakeCmdBuildRelease

assimpRootBuildDir = 'assimp--{dotVersion}.{svnRevision}-source-only'.format( dotVersion=descriptorVersionDot, svnRevision=svnRevision )
absRootBuildDir = os.path.join( buildDirectory, descriptorName + descriptorVersion, assimpRootBuildDir )

if CCVersionNumber in [8, 9, 10, 11, 12]:
	options = 	' -D BOOST_ROOT="{localExt}/include" '.format( localExt=localExtDirectory )
	options += ' -D BUILD_ASSIMP_TOOLS=OFF ' # so dx9 is no more needed
else:
	print >>sys.stderr, "Wrong MSVC version. Version 8.0[Exp], 9.0[Exp], 10.0[Exp], 11.0[Exp] or 12.0[Exp] required."
	exit(1)

descriptor = {

	'urls':		[	'http://sourceforge.net/projects/assimp/files/assimp-{dotVersion}/assimp--{dotVersion}.{svnRevision}-source-only.zip/download'.format(dotVersion=descriptorVersionDot, svnRevision=svnRevision) ],

	'name'		:	descriptorName,
	'version'	:	descriptorVersion,

	'rootBuildDir'	: assimpRootBuildDir,
	'builds'		: [ getCMakeCmdConfigure(CCVersionNumber, options), getCMakeCmdBuildDebug(), getCMakeCmdBuildRelease() ],


	'rootDir'		: assimpRootBuildDir,

	'include'		: [ ('include/assimp/', 'assimp/') ],

	'lib'			:	[	# debug
							'lib/Debug/assimpD.lib', 'bin/Debug/*.pdb', 'bin/Debug/*.dll',
							# release
							'lib/Release/assimp.lib', 'bin/Release/*.dll',
							],

	'license'		:	[ 'LICENSE' ]
}
