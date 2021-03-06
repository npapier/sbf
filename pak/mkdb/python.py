#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for cl 10.0 and 11.0 (32/64 bits), gcc

from os.path import basename, dirname, join
import shutil

# http://www.python.org

descriptorName = 'python'

descriptorVersion = '2-7-3'
#descriptorVersion = '2-7-8'

# Remarks :
# * Python-2.7.3_clXX-0Exp.zip contains converted solution and Visual C++ project.
# * _tkinter, _hashlib and _ssl projects are removed from the Visual C++ solution
# * for cl11: remove _msi project too (from the Visual C++ solution)

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

urls = [	'http://python.org/ftp/python/{version}/Python-{version}.tgz'.format(version=descriptorVersionDot),
		# berkeley-db
		'http://download.oracle.com/berkeley-db/db-4.7.25.tar.gz',
		# bzip2
		'http://www.bzip.org/1.0.5/bzip2-1.0.5.tar.gz',
		# sqlite
		'http://www.sqlite.org/sqlite-amalgamation-3.6.21.tar.gz'	]

builds = [	compilePYC(join(absRootBuildDir, projectFolderName, 'Lib'), pythonLibs),
			configureBDB(absRootBuildDir, join(absRootBuildDir, projectFolderName, 'PCbuild')) ]

if platform == 'win':
	urls.append( '$SRCPAKPATH/Python-{version}_{ccVersion}.zip'.format(version=descriptorVersionDot, ccVersion=CCVersion) )

	ConfigureVisualStudioVersion(CCVersionNumber)

	if CCVersionNumber >= 10:
		sln = join( absRootBuildDir, projectFolderName, 'PCbuild', 'pcbuild.sln' )

		if arch == 'x86-32':
			myPlatform = 'Win32'
			relPathToBin = ''
		else:
			myPlatform = 'x64'
			relPathToBin = 'amd64/'

		cmdDebug	= GetMSBuildCommand( dirname(sln), basename(sln), config = 'Debug', maxcpucount = cpuCount, platform = myPlatform )
		cmdRelease	= GetMSBuildCommand( dirname(sln), basename(sln), config = 'Release', maxcpucount = cpuCount, platform = myPlatform )
		builds.extend( [cmdDebug, cmdRelease] )

		rootDir = join(projectFolderName, 'PCbuild')
		license = ['../LICENSE']
		include = [('../Include', 'Python/'), ('../PC/pyconfig.h', 'Python/')]
		lib = ['{}python27*.lib'.format(relPathToBin), '{}python27*.pdb'.format(relPathToBin)]

		runtimeCustom = [(GlobRegEx('../PC/py.?\.ico'), 'bin/DLLs/'),
						 (GlobRegEx('../Lib/.+', pruneDirs='(?:test)|(?:plat-.+)', recursive=True), 'bin/Lib/')]

		binR = [GlobRegEx('{}python(?:|w|27)[.](?:dll|exe)'.format(relPathToBin))]
		runtimeCustomR = [('{}sqlite3.dll'.format(relPathToBin), 'bin/DLLs/'), (GlobRegEx('{}[^\.]+(?<!_d)[.]pyd'.format(relPathToBin)), 'bin/DLLs/')]

		binD = [GlobRegEx('{}python(?:|w|27)_d[.](?:dll|exe)'.format(relPathToBin))]
		runtimeCustomD = [('{}sqlite3_d.dll'.format(relPathToBin), 'bin/DLLs/'), (GlobRegEx('{}[^\.]+(?<=_d)[.]pyd'.format(relPathToBin)), 'bin/DLLs/')]
	else:
		print ('Given unsupported MSVC version {}. \nVersion 10.0[Exp] or 11.0[Exp] required.'.format(ccVersionNumber))
		exit(1)
else:
	exit(1)
	# @todo the generated python is not very movable in the filesystem (pb with sys.path and sys.prefix containing --prefix from ./configure!!!

	#--prefix=`pwd`/../install --exec-prefix=`pwd`/../install_arch
	import os
	os.environ['DESTDIR'] = join(absRootBuildDir, 'install')
	builds.extend( GetAutoconfBuildingCommands("--enable-shared --prefix='/'") )

	rootDir = 'install'
	license = [join('..', projectFolderName, 'LICENSE')]
	include = ['include/', (join('..', projectFolderName, 'pyconfig.h'), 'python2.7/')]
	lib = []

	runtimeCustom = [ (GlobRegEx('lib/python2.7/.+', pruneDirs='(?:test)|(?:plat-.+)', recursive=True), 'bin/lib/')]

	binR = ['bin/python', 'bin/python2', 'bin/python2.7', 'lib/libpython2.7.so*']
	runtimeCustomR = []

	binD = []
	runtimeCustomD = []

descriptor = {
	'urls'			: urls,

	'name'			: descriptorName,
	'version'		: descriptorVersion,

	'rootBuildDir'	: projectFolderName,
	'builds'		: builds,

	# packages developer and runtime
	'rootDir'		: rootDir,

	# developer package 
	'license'		: license,
	'include'		: include,
	'lib'			: lib,

	# runtime package
	'runtimeCustom'	:	runtimeCustom,

	# runtime package (release version)
	'binR'				: binR,
	'runtimeCustomR'	: runtimeCustomR,

	# runtime package (debug version)
	'binD'				: binD,
	'runtimeCustomD'	: runtimeCustomD
}
