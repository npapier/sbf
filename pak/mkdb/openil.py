#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for cl9.0Exp

# http://openil.sourceforge.net/

import os.path

descriptorName = 'openil'
descriptorVersion = '1-7-8'
projetFolderName = 'devil-1.7.8'
libPath = 'lib/vc9/x86'

if CCVersionNumber == 9: 
	vcexpress = r"D:\Program Files (x86)\Microsoft Visual Studio 9.0\Common7\IDE\VCExpress.exe"
	sbfPath = os.getenv("SCONS_BUILD_FRAMEWORK")
	sln = os.path.join( sbfPath, 'pak', 'var', 'build', descriptorName + descriptorVersion, projetFolderName, 'projects', 'msvc9', 'ImageLib.sln' )
	cmdRelease = "\"{0}\" {1} /build Release /out outRelease.txt".format(vcexpress, sln)
else:
	print >>sys.stderr, "Wrong MSVC version. Version 9.0Exp Required."
	exit(1)

descriptor = {
 'urls'			: ['http://downloads.sourceforge.net/openil/DevIL-1.7.8.zip', 'http://orange/files/Dev/localExt/src/openil1-7-8_LibCompiled-vc9.zip', 'http://orange/files/Dev/localExt/src/openil1-7-8_PATCH.zip'],

 'rootBuildDir'	: projetFolderName,
 'builds'		: [	cmdRelease ],

 'name'			: descriptorName,
 'version'		: descriptorVersion,

 'rootDir'		: projetFolderName,
 'license'		: ['COPYING'],
 'include'		: [('include/IL/','IL/')],
 'lib'			: [ os.path.join(libPath, '*.dll'), os.path.join(libPath, '*.lib') ]
}

# ok for cl8.y
# descriptor = {
# 'urls'			: ['http://downloads.sourceforge.net/openil/DevIL-SDK-x86-1.7.8.zip'],

# 'name'			: 'openil',
# 'version'		: '1-7-8',

# 'license'		: ['COPYING'],
# 'include'		: ['include/'],
# 'lib'			: ['lib/*.dll', 'lib/*.lib']
#}
