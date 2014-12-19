#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2012, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Guillaume Brocker
# Author Nicolas Papier

# cl8, 9, 10, 11, 12 [Exp] and linux

descriptorName = 'openassetimport'
descriptorVersion = '3-0'
svnRevision = 1270
descriptorVersionDot = descriptorVersion.replace('-', '.')

print ('INFORMATIONS: boost have to be installed in localExt')

import os.path
from src.sbfCMake import getCMakeCmdConfigure, getCMakeCmdBuildDebug, getCMakeCmdBuildRelease

assimpRootBuildDir = 'assimp--{dotVersion}.{svnRevision}-source-only'.format( dotVersion=descriptorVersionDot, svnRevision=svnRevision )
absRootBuildDir = os.path.join( buildDirectory, descriptorName + descriptorVersion, assimpRootBuildDir )

if platform == 'win':
	lib = [	# debug
			'lib/Debug/assimpD.lib', 'bin/Debug/*.pdb',
			# release
			'lib/Release/assimp.lib' ]
	binR = ['bin/Release/*.dll']
	binD = ['bin/Debug/*.dll']
	options =  ' -D BOOST_ROOT="{localExt}/include" '.format( localExt=localExtDirectory )
elif platform == 'posix':
	lib  = []
	binR = ['lib/libassimp.so*'] # @todo Improve this since symbolic links to the same library file will result in copies in the final zip archive
	binD = []
	options = ''
else:
	print >>sys.stderr, "Platform {} not supported".format(platform)
	exit(1)

options += ' -D BUILD_ASSIMP_TOOLS=OFF ' # so dx9 is no more needed

# @todo parallel build

descriptor = {

	'urls':		[	'http://sourceforge.net/projects/assimp/files/assimp-{dotVersion}/assimp--{dotVersion}.{svnRevision}-source-only.zip'.format(dotVersion=descriptorVersionDot, svnRevision=svnRevision),
					'$SRCPAKPATH/assimp--3.0.1270-source-only-patch.zip' ],

	'name'		:	descriptorName,
	'version'	:	descriptorVersion + '-2',

	'rootBuildDir'	: assimpRootBuildDir,
	'builds'		: [ getCMakeCmdConfigure(CC, CCVersionNumber, arch, options), getCMakeCmdBuildDebug(), getCMakeCmdBuildRelease() ],

	#
	'rootDir'		: assimpRootBuildDir,

	# developer package
	'license'		:	[ 'LICENSE' ],

	'include'		: [ ('include/assimp/', 'assimp/') ],

	'lib'			:	lib,

	# runtime package (release version)
	'binR'			:	binR,

	# runtime package (debug version)
	'binD'			:	binD,
}
