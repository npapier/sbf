#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2013, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for clx.y

# http://www.zlib.net/

import os.path

major = 1
minor = 2
maintenance = 8
version = '{}-{}-{}'.format( major, minor, maintenance )
dotVersion = '{}.{}.{}'.format( major, minor, maintenance )

contribPath = 'contrib/vstudio/vc{}'.format(int(CCVersionNumber))

descriptor = {
 'urls'			: ['http://zlib.net/zlib-{}.tar.gz'.format(dotVersion)],

 'name'			: 'zlib',
 'version'		: version,

 # Build
 'rootBuildDir' : 'zlib-{}'.format(dotVersion),

 'builds'		: [	# Fix VERSION attribute of .def file (1.2.8 => 1.2)
					Patcher(join(contribPath, 'zlibvc.def'), [('(^VERSION		\d.\d).*$', '\\1')]),
					# Fix WinApi family selection
					Patcher('contrib/minizip/iowin32.c', [('^\#if WINAPI_FAMILY_PARTITION\(WINAPI_PARTITION_APP\)$', '#if WINAPI_FAMILY_ONE_PARTITION(WINAPI_FAMILY_DESKTOP_APP, WINAPI_PARTITION_APP)')]),
					# Add /SAFESEH:NO (Image has Safe Exception Handlers).
					Patcher(join(contribPath, 'zlibvc.vcxproj'), [('^(.*ImportLibrary.*ImportLibrary.*)$', '\\1\n      <ImageHasSafeExceptionHandlers>false</ImageHasSafeExceptionHandlers>\n')]),
					# /MP
					MSVC['AddMultiProcessorCompilation'](join(contribPath, 'zlibvc.vcxproj')),

					# Build Release
					GetMSBuildCommand(contribPath, 'zlibvc.sln', 'zlibvc', 'Release' ),

					# Build debug
					#	Patch output name
					Patcher(join(contribPath, 'zlibvc.vcxproj'), [('^(.*\$\(OutDir\))zlibwapi(\..*)$', '\\1zlibwapi-d\\2')] ),
					Patcher(join(contribPath, 'zlibvc.vcxproj'), [('^(.*TargetName Condition.*)zlibwapi(.*TargetName.*)$', '\\1zlibwapi-d\\2')] ),
					GetMSBuildCommand(contribPath, 'zlibvc.sln', 'zlibvc', 'Debug' ),
					],

 # packages developer and runtime
 # Use rootDir to do from the build directory a 'cd rootDir' in order to shorten all following commands.
 'rootDir'		: 'zlib-{}'.format(dotVersion),

 # developer package
 'license'		: ['README'],
 'include'		: [ ('zlib.h', 'zlib/'), ('zconf.h', 'zlib/') ],
 'lib'			: [ join(contribPath, 'x86/ZlibDllRelease', '*.lib'),
					join(contribPath, 'x86/ZlibDllDebug', '*.lib'),
					join(contribPath, 'x86/ZlibDllDebug', 'zlibwapi-d.pdb') ],

 # runtime package (release version)
 'binR'			: [join(contribPath, 'x86/ZlibDllRelease', '*.dll')],

 # runtime package (debug version)
 'binD'			: [join(contribPath, 'x86/ZlibDllDebug', '*.dll')]
}

#descriptor = {
# 'urls'			: ['http://zlib.net/zlib128-dll.zip'],

# 'name'			: 'zlib',
# 'version'		: '1-2-8',

 # developer package
# 'license'		: ['README.txt'],
# 'include'		: [ ('include/*.h', 'zlib/') ],
# 'lib'			: [ 'lib/zdll.lib'],

 # runtime package
# 'bin'			: [ 'zlib1.dll' ]
#}
