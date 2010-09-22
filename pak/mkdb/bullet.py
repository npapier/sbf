# SConsBuildFramework - Copyright (C) 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for cl9.0Exp

import os.path

descriptorName = 'bullet'
descriptorVersion = '2-76'
projetFolderName = 'bullet-2.76'
libPath = 'msvc/2008/src/'

if CCVersionNumber == 9: 
	vcexpress = r"C:\Program Files (x86)\Microsoft Visual Studio 9.0\Common7\IDE\VCExpress.exe"
	sbfPath = os.getenv("SCONS_BUILD_FRAMEWORK")
	sln = os.path.join( sbfPath, 'pak', 'var', 'build', descriptorName + descriptorVersion, projetFolderName, 'msvc', '2008', 'BULLET_PHYSICS.sln' )
	cmdDebug = "\"{0}\" {1} /build Debug /out outDebug.txt".format(vcexpress, sln)
	cmdRelease = "\"{0}\" {1} /build Release /out outRelease.txt".format(vcexpress, sln)
else:
	print >>sys.stderr, "Wrong MSVC version. Version 9.0Exp Required."
	exit(1)

descriptor = {
 'urls'				: ['http://bullet.googlecode.com/files/bullet-2.76.zip'],

 'rootBuildDir'		: projetFolderName,
 'builds'			: [	cmdRelease ],
 #'builds'			: [	cmdDebug, cmdRelease ],

 'name'				: descriptorName,
 'version'			: descriptorVersion,

 'rootDir'			: projetFolderName,
 'license'			: ['LICENSE'],
 'include'			: ['src/'],	# @todo filter files (remove at least *.cpp)
 'lib'				: [	libPath + 'BulletCollision/Release/BulletCollision.lib',
						libPath + 'BulletDynamics/Release/BulletDynamics.lib',
						libPath + 'BulletMultiThreaded/Release/BulletMultiThreaded.lib',
						libPath + 'BulletSoftBody/Release/BulletSoftBody.lib',
						libPath + 'LinearMath/Release/LinearMath.lib' ] # @todo debug version
					# @todo extras
}
