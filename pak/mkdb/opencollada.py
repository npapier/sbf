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

descriptorName = 'opencollada'
descriptorVersion = '768'

cmdVcprojPatcher = """python ../../../../mkdb/details/opencolladaPatcher.py"""
if CCVersionNumber == 9: 
	vcexpress = r"C:\Program Files (x86)\Microsoft Visual Studio 9.0\Common7\IDE\VCExpress.exe"
	sbfPath = os.getenv("SCONS_BUILD_FRAMEWORK")
	sln = os.path.join( sbfPath, 'pak', 'var', 'build', descriptorName + descriptorVersion, descriptorName, 'OpenCOLLADA.sln' )
	cmdDebug = "\"{0}\" {1} /build Debug_Max2010 /out outDebug.txt".format(vcexpress, sln)
	cmdRelease = "\"{0}\" {1} /build Release_Max2010 /out outRelease.txt".format(vcexpress, sln)	
else:
	print >>sys.stderr, "Wrong MSVC version. Version 9.0Exp Required."
	exit(1)



descriptor = {

 'svnUrl'		: 'http://opencollada.googlecode.com/svn/trunk',

 'urls'			: [	"http://orange/files/Dev/localExt/src/opencollada.zip" ], # MSVC solution + patch files.

 'rootBuildDir'	: descriptorName,
 'builds'		: [	cmdVcprojPatcher, cmdDebug, cmdRelease ],

 'name'			: descriptorName,
 'version'		: descriptorVersion,

 'rootDir'		: descriptorName,
 'license'		: [('COLLADAMax/LICENSE')],
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
 'lib'			: [	'COLLADAFramework/lib/win/Win32/Release/*.lib',
					('COLLADAFramework/lib/win/Win32/Debug/COLLADAFramework.lib', 'COLLADAFramework-d.lib'),
					'COLLADABaseUtils/lib/win/Win32/Release/*.lib',
					('COLLADABaseUtils/lib/win/Win32/Debug/COLLADABaseUtils.lib', 'COLLADABaseUtils-d.lib'),
					'COLLADASaxFrameworkLoader/lib/win/Win32/Release_LibXML/*.lib',
					('COLLADASaxFrameworkLoader/lib/win/Win32/Debug_LibXML_NoValidation/COLLADASaxFrameworkLoader.lib', 'COLLADASaxFrameworkLoader-d.lib'),
					'COLLADAStreamWriter/lib/win/Win32/Release/*.lib',
					('COLLADAStreamWriter/lib/win/Win32/Debug/COLLADAStreamWriter.lib', 'COLLADAStreamWriter-d.lib'),
					'GeneratedSaxParser/lib/win/Win32/Release_LibXML/*.lib',
					('GeneratedSaxParser/lib/win/Win32/Debug_LibXML/GeneratedSaxParser.lib', 'GeneratedSaxParser-d.lib'),
					'Externals/MathMLSolver/lib/win/Win32/Release/*.lib',
					('Externals/MathMLSolver/lib/win/Win32/Debug/MathMLSolver.lib', 'MathMLSolver-d.lib'),
					'Externals/LibXML/lib/win/Win32/Release/*.lib',
					('Externals/LibXML/lib/win/Win32/Debug/LibXML.lib', 'LibXML-d.lib'),
					'Externals/pcre/lib/win/Win32/Release/*.lib',
					('Externals/pcre/lib/win/Win32/Debug/pcre.lib', 'pcre-d.lib'),
					'common/libBuffer/lib/win/Win32/Release_lib/*.lib',
					('common/libBuffer/lib/win/Win32/Debug_lib/libBuffer.lib', 'libBuffer-d.lib'),
					'common/libftoa/lib/win/Win32/Release_lib/*.lib',
					('common/libftoa/lib/win/Win32/Debug_lib/libftoa.lib', 'libftoa-d.lib'),
					'G3DWarehouseBrowser/lib/win/Win32/Release/*.lib',
					('G3DWarehouseBrowser/lib/win/Win32/Debug/G3DWarehouseBrowser.lib', 'G3DWarehouseBrowser-d.lib')],
					
#'bin'			: [ ('COLLADAValidator/bin/win/Win32/Debug LibXML/COLLADAValidator_LibXML.exe', 'COLLADAValidator_LibXML-d.exe'),
#					('COLLADAValidator/bin/win/Win32/Release LibXML/COLLADAValidator_LibXML.exe', 'COLLADAValidator_LibXML.exe')]
}
