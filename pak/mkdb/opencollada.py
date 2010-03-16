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
	* open the VC solution of dae2ogre project and convert it to the VC9 format. (contains all reader libs)
	* rename build configuration "Debug LibXML and Release LibXML respectively to "Debug" and "Release".
	* save and quit.
	* open the VC solution of StreamWriter project and convert it to the VC9 format. (contains all writer libs)
	* create zip archive of the openCOLLADA folder and put it on orange.
	* update "projetFolderName" variable in opencollada.py file.
'''

if CCVersionNumber == 9: 
	vcexpress = r"C:\Program Files (x86)\Microsoft Visual Studio 9.0\Common7\IDE\VCExpress.exe"
	sbfPath = os.getenv("SCONS_BUILD_FRAMEWORK")
	projetFolderName = 'opencollada736'
	dae2ogreSln = os.path.join( sbfPath, 'pak', 'var', 'build', projetFolderName, projetFolderName, 'dae2ogre', 'dae2ogre.sln' )
	streamWriterSln = os.path.join( sbfPath, 'pak', 'var', 'build', projetFolderName, projetFolderName, 'COLLADAStreamWriter', 'COLLADAStreamWriter.sln' )
	cmdDae2ogreDebug = "\"{0}\" {1} /build Debug /out outDebug.txt".format(vcexpress, dae2ogreSln)
	cmdDae2ogreRelease = "\"{0}\" {1} /build Release /out outRelease.txt".format(vcexpress, dae2ogreSln)
	cmdStreamWriterDebug = "\"{0}\" {1} /build Debug /out outDebug.txt".format(vcexpress, streamWriterSln)
	cmdStreamWriterRelease = "\"{0}\" {1} /build Release /out outRelease.txt".format(vcexpress, streamWriterSln)	
	
else:
	print >>sys.stderr, "Wrong MSVC version. Version 9.0Exp Required."
	exit(1)



descriptor = {
 'urls'			: [	"http://orange/files/Dev/localExt/src/opencollada736.zip" ],

 'rootBuildDir'	: 'opencollada736',
 'builds'		: [	cmdDae2ogreDebug, cmdDae2ogreRelease, cmdStreamWriterDebug, cmdStreamWriterRelease ],

 'name'			: 'opencollada',
 'version'		: '736',

 'rootDir'		: 'opencollada736',
 
 #'license'		: ['LICENSE_1_0.txt'],
 
 'include'		: [	('COLLADAFramework/include/', 'opencollada/COLLADAFramework/'),
					('COLLADABaseUtils/include/', 'opencollada/COLLADABaseUtils/'),
					('COLLADASaxFrameworkLoader/include/', 'opencollada/COLLADASaxFrameworkLoader/'),
					('COLLADAStreamWriter/include/', 'opencollada/COLLADAStreamWriter/'),
					('GeneratedSaxParser/include/', 'opencollada/GeneratedSaxParser/'),
					('Externals/MathMLSolver/include/', 'opencollada/MathMLSolver/'),
					('Externals/LibXML/include/', 'opencollada/LibXML/'),
					('Externals/pcre/include/', 'opencollada/pcre/'),
					('common/libBuffer/include', 'opencollada/libBuffer/'),
					('common/libftoa/include', 'opencollada/libftoa/')],

 'lib'			: [	'COLLADAFramework/lib/win/win32/*.lib',
					'COLLADABaseUtils/lib/win/win32/*.lib',
					'COLLADASaxFrameworkLoader/lib/win/win32/LibXML/*.lib',
					'COLLADAStreamWriter/lib/win/Win32/*.lib',
					'GeneratedSaxParser/lib/win/win32/LibXML/*.lib',
					'Externals/MathMLSolver/lib/win/win32/*.lib',
					'Externals/LibXML/bin/win/win32/*.lib',
					'Externals/pcre/lib/win/win32/*.lib',
					('common/libBuffer/lib/win/Win32/Debug lib/libBuffer.lib', 'libBuffer-d.lib'),
					'common/libBuffer/lib/win/Win32/Release lib/*.lib',
					('common/libftoa/lib/win/Win32/Debug lib/libftoa.lib', 'libftoa-d.lib'),
					'common/libftoa/lib/win/Win32/Release lib/*.lib']
}
