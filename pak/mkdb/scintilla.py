#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# cl8,9,10,11[Exp]

# requirement: qmake

# http://www.scintilla.org/

descriptorName = 'scintilla'
versionMajor = 3
versionMinor = 2
versionMaintenance = 3
descriptorVersion = '{major}{minor}{maintenance}'.format(major=versionMajor, minor=versionMinor, maintenance=versionMaintenance)
descriptorDotVersion = '{major}.{minor}.{maintenance}'.format(major=versionMajor, minor=versionMinor, maintenance=versionMaintenance)
descriptorDashVersion = '{major}-{minor}-{maintenance}'.format(major=versionMajor, minor=versionMinor, maintenance=versionMaintenance)

import os
from src.sbfQt import getQMakePlatform

if CCVersionNumber not in [8, 9, 10, 11]:
	print >>sys.stderr, "Wrong MSVC version. Version 8.0[Exp], 9.0[Exp], 10.0[Exp] or 11.0[Exp] required."
	exit(1)

os.environ['QTDIR'] = 'D:\\Qt\\4.8.0'
os.environ['PATH'] = 'D:\\Qt\\4.8.0\\bin' + os.pathsep + os.environ['PATH']

def myVCCmd( cmd, execCmdInVCCmdPrompt = execCmdInVCCmdPrompt ):
	return lambda : execCmdInVCCmdPrompt(cmd)

currentPlatform = getQMakePlatform( CCVersionNumber )

absRootBuildDir = os.path.join( buildDirectory, descriptorName + descriptorDashVersion, descriptorName )
def qtIncludesPatcher( directory ):
	def _patcher( directory ):
		# Search files to patch
		from src.sbfFiles import searchFiles
		files = []
		searchFiles( join(directory, 'qt', 'ScintillaEditBase'), files, [], allowedFilesRe = r".*[.]h" )
		searchFiles( join(directory, 'qt', 'ScintillaEdit'), files, [], allowedFilesRe = r".*[.]h" )

		# Patches files
		for absFilename in files:
			# Reads the whole file
			with open( absFilename ) as file:
				lines = file.readlines()
			# Do the patch
			for (i,line) in enumerate(lines):
				line = line.replace('slots', 'Q_SLOTS', 1)
				line = line.replace('signals', 'Q_SIGNALS', 1)
				lines[i] = line
			# Writes the patch
			with open( absFilename, 'w' ) as file:
				# Writes modifications
				file.writelines( lines )
	return lambda : _patcher( directory )

descriptor = {
 'urls'		: ['http://sourceforge.net/projects/scintilla/files/scintilla/{dotVersion}/scintilla{version}.zip/download'.format(dotVersion=descriptorDotVersion, version=descriptorVersion)],

 'rootBuildDir'	: descriptorName,
 'builds'		: [	# ScintillaEdit.h and ScintillaEdit.cpp files will have been populated with the Scintilla API methods.
					'cd qt/ScintillaEdit && python WidgetGen.py',
					# Build release version
					myVCCmd('cd qt/ScintillaEdit && qmake -platform {platform} ScintillaEdit.pro'.format(platform=currentPlatform)),
					myVCCmd('cd qt/ScintillaEdit && nmake -f Makefile release'),
					# Build debug version
					myVCCmd('cd qt/ScintillaEdit && qmake -platform {platform} -after "TARGET=ScintillaEditD" ScintillaEdit.pro'.format(platform=currentPlatform)),
					myVCCmd('cd qt/ScintillaEdit && nmake -f Makefile debug'),
					# Patch include files (slots => Q_SLOTS, signals => Q_SIGNALS)
					qtIncludesPatcher(absRootBuildDir)
					],

 'name'			: descriptorName,
 'version'		: descriptorDashVersion,

 'rootDir'		: descriptorName,

 'lib'			: [ 'bin/*.dll', 'bin/*.lib', 'bin/*.pdb' ],

 'include'		: [	('include/*.h', 'Scintilla/'),
					('qt/ScintillaEditBase/*.h', 'Scintilla/'),
					('qt/ScintillaEdit/*.h', 'Scintilla/') ],

 'license'		: [ 'License.txt' ]
}
