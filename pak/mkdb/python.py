#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2013, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for cl10.0
# nok for cl11.0. Still linked with cl10 runtime !!! Look at <PlatformToolset>v110</PlatformToolset> in .vcxproj ?

from os.path import join
import shutil

# http://www.python.org

descriptorName = 'python'

descriptorVersion = '2-7-3'
# Remarks :
# * Python-2.7.3_cl10-0Exp.zip contains converted solution and Visual C++ project.
# * _tkinter, _hashlib and _ssl projects are removed from the Visual C++ solution

pythonLibs = [	'bsddb', 'compiler', 'ctypes', 'curses', 'distutils', 'email', 'encodings', 'hotshot',
				'idlelib', 'importlib', 'json', 'lib-tk', 'lib2to3', 'logging', 'msilib', 'multiprocessing',
				'pydoc_data', 'site-packages', 'sqlite3',
				#'test',
				'unittest', 'wsgiref', 'xml']

descriptorVersionDot = descriptorVersion.replace('-', '.')
absRootBuildDir = join(buildDirectory, descriptorName + descriptorVersion )
projectFolderName = 'Python-{0}'.format(descriptorVersionDot)


# Berkeley DB
def configureBDB( src, dst ):
	def _configureBDB( src, dst ):
		import glob
		import os
		import shutil
		shutil.move( join(src, 'db-4.7.25'), join(src, 'db-4.7.25.0') )
		for elt in glob.glob(join(src, 'db-4.7.25.0', '*')):
			if os.path.isdir(elt):
				shutil.copytree( elt, join(dst, os.path.basename(elt)) )
	return lambda : _configureBDB(src, dst)

# Compile .py into .pyc
def compilePYC( directory, pythonLibs ):
	def _compilePYC( directory, pythonLibs ):
		import compiler
		import os

		# Collect .py files
		files = []
		pythonLibsSet = set( pythonLibs )
		for dirpath, dirnames, filenames in os.walk( directory ):
			for dir in dirnames[:]:
				if dir not in pythonLibsSet:
					dirnames.remove(dir)
			for file in filenames:
				if os.path.splitext(file)[1] == '.py':
					files.append( os.path.join(dirpath,file) )
		# Compile .py into .pyc
		for file in files:
			compiler.compileFile( file )
	return lambda : _compilePYC(directory, pythonLibs)

#
if CCVersionNumber >= 10:
	sln = join( absRootBuildDir, projectFolderName, 'PCbuild', 'pcbuild.sln' )
	cmdDebug = "\"{0}\" {1} /build Debug /out outDebug.txt".format(MSVSIDE, sln)
	cmdRelease = "\"{0}\" {1} /build Release /out outRelease.txt".format(MSVSIDE, sln)
else:
	print >>sys.stderr, "Unsupported MSVC version."
	exit(1)


descriptor = {
	'urls'			: [	'http://python.org/ftp/python/{version}/Python-{version}.tar.xz'.format(version=descriptorVersionDot),
						'http://orange/files/Dev/localExt/src/Python-{version}_{ccVersion}.zip'.format(version=descriptorVersionDot, ccVersion=CCVersion),
						# berkeley-db
						'http://download.oracle.com/berkeley-db/db-4.7.25.tar.gz',
						# bzip2
						'http://www.bzip.org/1.0.5/bzip2-1.0.5.tar.gz',
						# sqlite
						'http://www.sqlite.org/sqlite-amalgamation-3.6.21.tar.gz',
						],

	'name'			: descriptorName,
	'version'		: descriptorVersion,

	'rootBuildDir'	: projectFolderName,
	'builds'		: [	compilePYC(join(absRootBuildDir, projectFolderName, 'Lib'), pythonLibs),
						configureBDB(absRootBuildDir, join(absRootBuildDir, projectFolderName, 'PCbuild')),
						cmdDebug, cmdRelease ],

	# packages developer and runtime
	'rootDir'		: join(projectFolderName, 'PCbuild'),

	# developer package 
	'license'		: ['../LICENSE'],
	'include'		: [('../Include', 'Python/'), ('../PC/pyconfig.h', 'Python/')],
	'lib'			: ['python27*.lib', 'python27*.pdb'],

	# runtime package
	'runtimeCustom'	:	[(GlobRegEx('../PC/py.?\.ico'), 'bin/DLLs/'),
						 (GlobRegEx('../Lib/.+', pruneDirs='(?:test)|(?:plat-.+)', recursive=True), 'bin/Lib/')],

	# runtime package (release version)
	'binR'				: [GlobRegEx('python(?:|w|27)[.](?:dll|exe)')],
	'runtimeCustomR'	: [('sqlite3.dll', 'bin/DLLs/'), (GlobRegEx('[^\.]+(?<!_d)[.]pyd'), 'bin/DLLs/')],

	# runtime package (debug version)
	'binD'				: [GlobRegEx('python(?:|w|27)_d[.](?:dll|exe)')],
	'runtimeCustomD'	: [('sqlite3_d.dll', 'bin/DLLs/'), (GlobRegEx('[^\.]+(?<=_d)[.]pyd'), 'bin/DLLs/')],
}
