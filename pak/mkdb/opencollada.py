#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SConsBuildFramework - Copyright (C) 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier
# Author Maxime Peresson

# cl9-0Exp

import os.path

print 	'''
/!\ IMPORTANT /!\
To create the zip file:
	* make an export of openCOLLADA project from the googlecode repository : http://code.google.com/p/opencollada/
	* open the VC solution of dae2ogre project and convert it to the VC9 format.
	* rename build configuration "Debug LibXML and Release LibXML respectively to "Debug" and "Release".
	* save and quit.
	* create zip archive of the openCOLLADA folder and put it on orange.
	* update "projetFolderName" variable.
'''

if CCVersionNumber == 9: 
	vcexpress = r"C:\Program Files (x86)\Microsoft Visual Studio 9.0\Common7\IDE\VCExpress.exe"
	sbfPath = os.getenv("SCONS_BUILD_FRAMEWORK")
	projetFolderName = 'opencollada736'
	sln = os.path.join( sbfPath, 'pak', 'var', 'build', projetFolderName, projetFolderName, 'dae2ogre', 'dae2ogre.sln' )
	cmdDebug = "\"{0}\" {1} /build Debug /out outDebug.txt".format(vcexpress, sln)
	cmdRelease = "\"{0}\" {1} /build Release /out outRelease.txt".format(vcexpress, sln)
	
else:
	print >>sys.stderr, "Wrong MSVC version. Version 9.0Exp Required."
	exit(1)



descriptor = {
 'urls'			: [	"http://orange/files/Dev/localExt/src/opencollada736.zip" ],

 'rootBuildDir'	: 'opencollada736',
 'builds'		: [	cmdDebug, cmdRelease ],

 'name'			: 'opencollada',
 'version'		: '736',

 'rootDir'		: 'opencollada736',
 
 #'license'		: ['LICENSE_1_0.txt'],
 
 'include'		: [	('COLLADAFramework/include/', 'opencollada/COLLADAFramework/'),
					('COLLADABaseUtils/include/', 'opencollada/COLLADABaseUtils/'),
					('COLLADASaxFrameworkLoader/include/', 'opencollada/COLLADASaxFrameworkLoader/'),
					('GeneratedSaxParser/include/', 'opencollada/GeneratedSaxParser/'),
					('Externals/MathMLSolver/include/', 'opencollada/MathMLSolver/'),
					('Externals/LibXML/include/', 'opencollada/LibXML/'),
					('Externals/pcre/include/', 'opencollada/pcre/')],

 'lib'			: [	'COLLADAFramework/lib/win/win32/*.lib',
					'COLLADABaseUtils/lib/win/win32/*.lib',
					'COLLADASaxFrameworkLoader/lib/win/win32/LibXML/*.lib',
					'GeneratedSaxParser/lib/win/win32/LibXML/*.lib',
					'Externals/MathMLSolver/lib/win/win32/*.lib',
					'Externals/LibXML/bin/win/win32/*.lib',
					'Externals/pcre/lib/win/win32/*.lib']
}
