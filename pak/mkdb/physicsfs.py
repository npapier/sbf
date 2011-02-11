#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier
# Author Maxime Peresson

# cl9-0Exp

import os.path

# http://icculus.org/physfs/
# MSVC solution is created with CMake.

if CCVersionNumber == 9: 
	vcexpress = r"C:\Program Files (x86)\Microsoft Visual Studio 9.0\Common7\IDE\VCExpress.exe"
	sbfPath = os.getenv("SCONS_BUILD_FRAMEWORK")
	projetFolderName = 'physfs2-0-1'
	sln = os.path.join( sbfPath, 'pak', 'var', 'build', projetFolderName, projetFolderName, 'bin', 'PhysicsFS.sln' )
	cmdDebug = "\"{0}\" {1} /build Debug /project physfs /out outDebug.txt".format(vcexpress, sln)
	cmdRelease = "\"{0}\" {1} /build Release /project physfs /out outRelease.txt".format(vcexpress, sln)
	
else:
	print >>sys.stderr, "Wrong MSVC version. Version 9.0Exp Required."
	exit(1)

descriptor = {
 'urls'			: [	'http://orange/files/Dev/localExt/src/physfs-2-0-1.zip' ],

 'rootBuildDir'	: 'physfs2-0-1',
 'builds'		: [	cmdDebug, cmdRelease ],

 'name'			: 'physfs',
 'version'		: '2-0-1',

 'rootDir'		: 'physfs2-0-1',
 
 'license'		: [('LICENSE.txt')],
 
 'include'		: [	'*.h' ],

'lib'			: [	'bin/Release/physfs.lib', 
					'bin/Release/physfs.dll',
					'bin/Debug/physfs-d.lib',
					'bin/Debug/physfs-d.dll' ],
}
