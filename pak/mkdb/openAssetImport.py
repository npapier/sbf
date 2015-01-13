#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2012, 2014, 2015, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Guillaume Brocker
# Author Nicolas Papier

# cl8, 9, 10, 11, 12 [Exp], emcc and linux

descriptorName = 'openassetimport'
descriptorVersion = '3-0'
svnRevision = 1270
descriptorVersionDot = descriptorVersion.replace('-', '.')

import os.path
from src.sbfCMake import getCMakeCmdConfigure, getCMakeCmdBuildDebug, getCMakeCmdBuildRelease

assimpRootBuildDir = 'assimp--{dotVersion}.{svnRevision}-source-only'.format( dotVersion=descriptorVersionDot, svnRevision=svnRevision )
absRootBuildDir = os.path.join( buildDirectory, descriptorName + descriptorVersion, assimpRootBuildDir )

RequiredProgram('cmake')
RequiredLibrary('boost')

builds = []
if svnRevision == 1270:
	builds += [	# Patch for version 3.0
				# 198: return Couple<T>(db).MustGetObject(To<EXPRESS::ENTITY>())->To<T>();
				#      return Couple<T>(db).MustGetObject(To<EXPRESS::ENTITY>())->template To<T>();
				Patcher('code/StepFile.h', [('\-\>To\<T\>\(\)', '->template To<T>()')]),
				# 204:	return e?Couple<T>(db).MustGetObject(*e)->ToPtr<T>():(const T*)0; =>
				#		return e?Couple<T>(db).MustGetObject(*e)->template ToPtr<T>():(const T*)0;
				Patcher('code/StepFile.h', [('\-\>ToPtr\<T\>\(\)\:', '->template ToPtr<T>():')])]
# else pass

if platform == 'win':
	options =  ' -D Boost_INCLUDE_DIR="{localExt}/include" '.format( localExt=localExtDirectory )
	options += ' -D BUILD_ASSIMP_TOOLS=OFF ' # so dx9 is no more needed
	if CC == 'cl':
		builds += [getCMakeCmdConfigure(CC, CCVersionNumber, arch, options), getCMakeCmdBuildDebug(), getCMakeCmdBuildRelease()]
		lib = [	# debug
				'lib/Debug/assimpD.lib', 'bin/Debug/*.pdb',
				# release
				'lib/Release/assimp.lib' ]
		binR = ['bin/Release/*.dll']
		binD = ['bin/Debug/*.dll']
	elif CC == 'emcc':							# @todo debug version
		options += ' -D BUILD_STATIC_LIB=ON '	# @todo dont work -D CMAKE_DEBUG_POSTFIX=-d
		builds += [	#
					getCMakeCmdConfigure(CC, CCVersionNumber, arch, options),
					# debug
					#getCMakeCmdBuildDebug(),
					#
					getCMakeCmdBuildRelease()]
		lib = [	# debug
				#'lib/libassimp-d.a', 'lib/libz-d.a',
				# release
				'lib/libassimp.a', 'lib/libz.a' ]
		binR = []
		binD = []

elif platform == 'posix':
	builds += [getCMakeCmdConfigure(CC, CCVersionNumber, arch, options), getCMakeCmdBuildDebug(), getCMakeCmdBuildRelease()]
	lib  = []
	binR = ['lib/libassimp.so*'] # @todo Improve this since symbolic links to the same library file will result in copies in the final zip archive
	binD = []
	options = ''
else:
	print >>sys.stderr, "Platform {} not supported".format(platform)
	exit(1)


# @todo parallel build

descriptor = {

	'urls'			:	[	'http://sourceforge.net/projects/assimp/files/assimp-{dotVersion}/assimp--{dotVersion}.{svnRevision}-source-only.zip'.format(dotVersion=descriptorVersionDot, svnRevision=svnRevision),
							'$SRCPAKPATH/assimp--3.0.1270-source-only-patch.zip' ],

	'name'			:	descriptorName,
	'version'		:	descriptorVersion + '-2',

	'rootBuildDir'	:	assimpRootBuildDir,
	'builds'		:	builds,

	#
	'rootDir'		:	assimpRootBuildDir,

	# developer package
	'license'		:	[ 'LICENSE' ],

	'include'		:	[ ('include/assimp/', 'assimp/') ],

	'lib'			:	lib,

	# runtime package (release version)
	'binR'			:	binR,

	# runtime package (debug version)
	'binD'			:	binD,
}
