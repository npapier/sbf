#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier
# Author Maxime Peresson

# cl9-0Exp

import os.path

print 	'''
/!\ WARNING /!\
To create the zip file:
	* make an export of openCOLLADA project from the googlecode repository : http://code.google.com/p/opencollada/
	* copy our "OpenCOLLADA.sln" in root directory or create it : it must contain:
		* pcre (debug: debug / release: release)				
		* libBuffer (debug: debug lib / release: release lib)
		* libftoa (debug: debug lib / release: release lib)
		* LibXML (debug: debug / release: release)
		* expat_static (debug: debug / release: release)		
		* MathMLSolver (debug: debug / release: release)
		* GeneratedSaxParser (debug: debug LibXML / release: release LibXML)		
		* COLLADABaseUtils (debug: debug / release: release)		
		* COLLADAFramework (debug: debug / release: release)
		* COLLADAStreamWriter (debug: debug / release: release)		
		* COLLADASaxFrameworkLoader (debug: debug LibXML / release: release LibXML)
		* COLLADAValidator (debug: debug LibXML / release: release LibXML)
		* G3DWarehouseBrowser (debug: debug / release: release)
	* take care of the build order / dependencies.
	* open it and convert all projects to the VC9 format.
	* save and quit.
	* create zip archive of the openCOLLADA folder and put it on orange.
	* update "projetFolderName" variable in opencollada.py file.
'''

if CCVersionNumber == 9: 
	vcexpress = r"C:\Program Files (x86)\Microsoft Visual Studio 9.0\Common7\IDE\VCExpress.exe"
	sbfPath = os.getenv("SCONS_BUILD_FRAMEWORK")
	projetFolderName = 'opencollada736'
	sln = os.path.join( sbfPath, 'pak', 'var', 'build', projetFolderName, projetFolderName, 'OpenCOLLADA.sln' )
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
					'common/libftoa/lib/win/Win32/Release lib/*.lib',
					('G3DWarehouseBrowser/lib/win/Win32/Debug/G3DWarehouseBrowser.lib', 'G3DWarehouseBrowser-d.lib'),
					'G3DWarehouseBrowser/lib/win/Win32/Release/*.lib'],
					
'bin'			: [ ('COLLADAValidator/bin/win/Win32/Debug LibXML/COLLADAValidator_LibXML.exe', 'COLLADAValidator_LibXML-d.exe'),
					('COLLADAValidator/bin/win/Win32/Release LibXML/COLLADAValidator_LibXML.exe', 'COLLADAValidator_LibXML.exe')]
}
