#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for clx.y

# http://www.cryptopp.com/

import os.path

major = 5
minor = 6
maintenance = 2
ver = '{}{}{}'.format(major, minor, maintenance)
version = '{}-{}-{}'.format( major, minor, maintenance )
dotVersion = '{}.{}.{}'.format( major, minor, maintenance )

if platform == 'win':
	vcxproj = 'cryptlib.vcxproj'
	sln = 'cryptest.sln'
	ConfigureVisualStudioVersion(CCVersionNumber)
else:
	print ("Platform '{}' not supported".format(platform))
	exit(1)

descriptor = {
 'urls'			: ['http://www.cryptopp.com/cryptopp{}.zip'.format(ver), '$SRCPAKPATH/cryptopp5-6-2_vcxproj.zip'],

 'name'			: 'cryptopp',
 'version'		: version,

 # Build
 'builds'		: [	# Fixes vcproj files
					#	Configures which version of cl have to be invoke.
					MSVC['SetPlatformToolset']( vcxproj, CCVersionNumber ),
					#	<RuntimeLibrary>MultiThreaded</RuntimeLibrary> => <RuntimeLibrary>MultiThreadedDLL</RuntimeLibrary>
					ChangeContentOfAnXMLElement(vcxproj, 'RuntimeLibrary', 'MultiThreaded', 'MultiThreadedDLL'),
					# Build Release
					GetMSBuildCommand('', sln, 'cryptlib', 'Release' ),

					# @todo ?
					# Build debug
					#	Patch output name
					#MSVC['ChangeTargetName']( vcxproj, 'cryptlib', 'cryptlib-d' ),
					#GetMSBuildCommand('', sln, 'cryptlib', 'Debug' ),
					],

 # packages developer and runtime
 # developer package
 'license'		: ['Readme.txt', 'License.txt'],
 'include'		: [ ('*.h', 'cryptopp/') ],
 'lib'			: [ 'Win32/Output/Release/cryptlib.lib' ],
}
