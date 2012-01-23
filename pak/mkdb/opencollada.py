#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2010, 2011, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier
# Author Maxime Peresson

# cl9-0Exp

import os.path
import re
import sys

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
'''

descriptorName = 'opencollada'
descriptorVersion = '864'

absRootBuildDir = os.path.join( buildDirectory, descriptorName + descriptorVersion, descriptorName )

# locate sbf and add it to sys.path
import os
import sys
sbf_root = os.getenv('SCONS_BUILD_FRAMEWORK')
if not sbf_root:
	raise StandardError("SCONS_BUILD_FRAMEWORK is not defined")
sbf_root_normalized	= os.path.normpath( os.path.expandvars( sbf_root ) )
sys.path.append( sbf_root_normalized )

def patcher( directory ):
	def executePatchWholeProgramOptimizationInVCPROJ( directory ):
		from src.sbfFiles import searchFiles
		from src.sbfVCProj import patchWholeProgramOptimizationInVCPROJ

		#
		vcprojFiles = []
		searchFiles( directory, vcprojFiles, ['.svn'], allowedFilesRe = r".*[.]vcproj" )

		# Patches each vcproj file found
		for vcprojFile in vcprojFiles:
			print ('Patching {0}'.format(vcprojFile))
			patchWholeProgramOptimizationInVCPROJ( vcprojFile )

	return lambda : executePatchWholeProgramOptimizationInVCPROJ(directory)



if CCVersionNumber == 9: 
	sln = os.path.join( absRootBuildDir, 'OpenCOLLADA.sln' )
	cmd = "\"{0}\" {1} /build {2}_Max2010 /out out{2}.txt"
	cmdDebug = cmd.format(MSVSIDE, sln, 'Debug')
	cmdRelease = cmd.format(MSVSIDE, sln, 'Release')
elif CCVersionNumber == 10:
	sln = os.path.join( absRootBuildDir, 'OpenCOLLADA.sln' )
	cmd = "\"{0}\" {1} /build {2}_Max2010 /out out{2}.txt"
	cmdDebug = cmd.format(MSVSIDE, sln, 'Debug')
	cmdRelease = cmd.format(MSVSIDE, sln, 'Release')
else:
	print >>sys.stderr, "Wrong MSVC version. Version 9.0[Exp] or 10.0[Exp] required."
	exit(1)



descriptor = {

 'svnUrl'		: 'http://opencollada.googlecode.com/svn/trunk@{0}'.format(descriptorVersion),

 'urls'			: [ "http://orange/files/Dev/localExt/src/opencollada{0}_{1}.zip".format(descriptorVersion, CCVersion) ], # MSVC solution [+ patch files].

 'rootBuildDir'	: descriptorName,
 'builds'		: [ patcher(absRootBuildDir), cmdDebug, cmdRelease ],

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
