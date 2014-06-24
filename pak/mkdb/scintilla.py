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
versionMaintenance = 4
descriptorVersion = '{major}{minor}{maintenance}'.format(major=versionMajor, minor=versionMinor, maintenance=versionMaintenance)
descriptorDotVersion = '{major}.{minor}.{maintenance}'.format(major=versionMajor, minor=versionMinor, maintenance=versionMaintenance)
descriptorDashVersion = '{major}-{minor}-{maintenance}'.format(major=versionMajor, minor=versionMinor, maintenance=versionMaintenance)

import os
import sys

from src.sbfQt import getQMakePlatform

def myVCCmd( cmd, execCmdInVCCmdPrompt = execCmdInVCCmdPrompt ):
	return lambda : execCmdInVCCmdPrompt(cmd)
	
currentPlatform = getQMakePlatform( CC, CCVersionNumber )

if platform == 'win32':
	if CCVersionNumber not in [8, 9, 10, 11]:
		print >>sys.stderr, "Wrong MSVC version. Version 8.0[Exp], 9.0[Exp], 10.0[Exp] or 11.0[Exp] required."
		exit(1)
	cmd  = [	# Build release version
			myVCCmd('cd qt/ScintillaEdit && qmake -platform {platform} ScintillaEdit.pro'.format(platform=currentPlatform)),
			myVCCmd('cd qt/ScintillaEdit && nmake -f Makefile release'),
			# Build debug version
			myVCCmd('cd qt/ScintillaEdit && qmake -platform {platform} -after "TARGET=ScintillaEditD" ScintillaEdit.pro'.format(platform=currentPlatform)),
			myVCCmd('cd qt/ScintillaEdit && nmake -f Makefile debug') ]
	lib  = [ 'bin/*.lib', 'bin/*.pdb' ]
	binR = [ GlobRegEx('bin/[^\.]+(?<!D3)[.]dll$') ]	# to match *3.dll without *D3.dll
	binD = [ GlobRegEx('bin/[^\.]+(?<=D3)[.]dll$') ]	# to match *D3.dll
else:
	cmd  = [	'cd qt/ScintillaEdit && qmake -platform {platform} ScintillaEdit.pro'.format(platform=currentPlatform),
			'cd qt/ScintillaEdit && make' ]
	lib  = []
	binR = [ 'bin/*.so*' ] # @todo Improve this since symbolic links to the same library file will result in copies in the final zip archive
	binD = []

os.environ['QTDIR'] = 'D:\\Qt\\4.8.0'
os.environ['PATH'] = 'D:\\Qt\\4.8.0\\bin' + os.pathsep + os.environ['PATH']

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
					# Patches the Scintilla.pro file in order to use the Scintilla namespace
					Patcher( 'qt/ScintillaEdit/ScintillaEdit.pro', [(r'^(DEFINES\s\+=\s)(.*)', r'\1 SCI_NAMESPACE=1 \2')] ),
					Patcher( 'qt/ScintillaEdit/ScintillaEdit.cpp', [(r'(^#include "ScintillaEdit.h")', r'\1\n\n#ifdef SCI_NAMESPACE\nusing namespace Scintilla;\n#endif')] ),
					Patcher( 'qt/ScintillaEdit/ScintillaDocument.cpp', [(r'(^#include "Document.h")', r'\1\n\n#ifdef SCI_NAMESPACE\nusing namespace Scintilla;\n#endif')] ) ]+
					cmd +
				  [
					# Patch include files (slots => Q_SLOTS, signals => Q_SIGNALS)
					qtIncludesPatcher(absRootBuildDir)
					],

 'name'			: descriptorName,
 'version'		: descriptorDashVersion,

 # packages developer and runtime
 'rootDir'		: descriptorName,

 # developer package
 'license'		: [ 'License.txt' ],
 'include'		: [	('include/*.h', 'Scintilla/'),
					('qt/ScintillaEditBase/*.h', 'Scintilla/'),
					('qt/ScintillaEdit/*.h', 'Scintilla/') ],
 'lib'			: lib,

 # runtime package
 #'bin'				: [],
 #'runtimeCustom'	: [],

 # runtime package (release version)
 'binR'			: binR,
 #'runtimeCustomR'	: [],

 # runtime package (debug version)
 'binD'			: binD,
 #'runtimeCustomD'	: [],
}
