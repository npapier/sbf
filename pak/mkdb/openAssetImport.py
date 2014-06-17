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

#print ('INFORMATIONS: boost have to be installed in localExt')

import os.path

from src.sbfCMake import getCMakeCmdConfigure, getCMakeCmdBuildDebug, getCMakeCmdBuildRelease

assimpRootBuildDir = 'assimp--{dotVersion}.{svnRevision}-source-only'.format( dotVersion=descriptorVersionDot, svnRevision=svnRevision )
absRootBuildDir = os.path.join( buildDirectory, descriptorName + descriptorVersion, assimpRootBuildDir )

if platform == 'win32':
	lib = [	# debug
			'lib/Debug/assimpD.lib', 'bin/Debug/*.pdb', 'bin/Debug/*.dll',
			# release
			'lib/Release/assimp.lib', 'bin/Release/*.dll' ]
	binR = ['bin/Release/*.dll']
	binD = ['bin/Debug/*.dll']	
	if CCVersionNumber in [8, 9, 10, 11, 12]:
		options =  ' -D BOOST_ROOT="{localExt}/include" '.format( localExt=localExtDirectory )
	else:
		print >>sys.stderr, "Wrong MSVC version. Version 8.0[Exp], 9.0[Exp], 10.0[Exp], 11.0[Exp] or 12.0[Exp] required."
		exit(1)
elif platform == 'posix':
	lib  = []
	binR = ['lib/libassimp.so'] #'lib/libassimp.so.3', 'lib/libassimp.so.3.0.1264'
	binD = []
	options = ''
	
options += ' -D BUILD_ASSIMP_TOOLS=OFF ' # so dx9 is no more needed
#options += " CMAKE_CXX_FLAGS+='-j4' " # @todo j4 hardcoded

descriptor = {

	'urls':		[	'http://sourceforge.net/projects/assimp/files/assimp-{dotVersion}/assimp--{dotVersion}.{svnRevision}-source-only.zip/download'.format(dotVersion=descriptorVersionDot, svnRevision=svnRevision),
					'http://orange/files/Dev/localExt/PUBLIC/src/assimp--3.0.1270-source-only-patch.zip'
	],

	'name'		:	descriptorName,
	'version'	:	descriptorVersion + '-2',

	'rootBuildDir'	: assimpRootBuildDir,
	'builds'		: [ getCMakeCmdConfigure(CC, CCVersionNumber, 'x86-32', options), getCMakeCmdBuildDebug(), getCMakeCmdBuildRelease() ],


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
