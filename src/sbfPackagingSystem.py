#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2008, 2009, 2010, 2011, 2012, 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import cPickle
import distutils.archive_util
import fnmatch
import glob
import multiprocessing
import os
import sbfAutoconf
import shutil
import subprocess
import types
import zipfile
from os.path import basename, dirname, exists, join, splitext

from sbfArchives import createArchive, extractArchive, extractAllTarFiles, getFilesAndDirectories
from sbfFiles import createDirectory, removeDirectoryTree, GlobRegEx, copy, removeFile, searchAllFilesAndDirectories, convertPathAbsToRel
from sbfSubversion import splitSvnUrl, Subversion
from sbfUses import UseRepository
from sbfUtils import removePathHead, executeCommandInVCCommandPrompt, getLambdaForExecuteCommandInVCCommandPrompt, createSConsBuildFrameworkProject, buildDebugAndReleaseUsingSConsBuildFramework
from sbfVersion import splitPackageName, joinPackageName


# see sbfVersion.py: splitPackageName() and sbfArchives.py: __extractExtensionAndFormat__()
defaultArchiveFormat = 'tar.bz2'
supportedArchiveFormats = [ defaultArchiveFormat, 'zip' ]

def isAGlobPattern( pattern ):
	globCharacters = set(['*', '?', '[', ']'])
	return len( set(list(pattern)) & globCharacters )>0

def pprintList( list ) :
	listLength = len(list)
	currentString = '[ '

	for i, element in enumerate(list):
		if len(currentString) + len(element) + 3 >= 120 :
			print currentString
			currentString = ''
		currentString += "'%s', " % element
	print currentString[0:-2] + " ]"



# Copy a file
# @todo move in another file : sbfFiles.py
def copyFile( source, destination, verbose = False, bufferSize = 1024 * 512 ):
	def _copyFile( source, destination, verbose ):
		if verbose:
			print ('Copying {0}...'.format(source))
		sourceStat = os.stat( source )
		fileSizeInKB = sourceStat.st_size/1024
		kBCopied = 0
		with open(source, 'rb') as src, open(destination, 'wb') as dst:
			while True:
				buffer = src.read(bufferSize)
				if buffer:
					dst.write(buffer)
					kBCopied += len(buffer)/1024
					# Prints report on advancement (each 512 kb)
					if (kBCopied % 512 == 0) and verbose:
							print ( '{0} / {1} kB \r'.format( kBCopied, fileSizeInKB ) ),
				else:
					break
		if verbose:
			print ('\rDone.' + ' ' * 40)

	if not os.path.exists( destination ):
		_copyFile( source, destination, verbose )
	else:
		destinationStat = os.stat( destination )
		sourceStat = os.stat( source )
		# @todo take care of mtime. pb with mtime on remote. sourceStat.st_mtime == destinationStat.st_mtime
		if	sourceStat.st_size == destinationStat.st_size:
			if verbose:
				print ('File {0} already copied'.format(source))
			return
		else:
			_copyFile( source, destination, verbose )



def reporthook_urlretrieve( blockCount, blockSize, totalSize ):
	size = blockCount * blockSize / 1024
	# Prints report on download advancement
	print ( '{} kB \r'.format(size) ),
	# Prints report on download advancement (each 128 kb)	
#	if ( size % 128 == 0):
#		print ( '{} kB \r'.format(size) ),
	#if totalSize > 0:
	#	print ( '%i kB, %i/%i' % ( size/1024, size, totalSize ) )
	#else:
	#	print ( '%i kB' % (size / 1024) )

def rsearchFilename( path ):
	if len(path) <= 1:
		return
	else:
		splitted = os.path.split(path)
		if len(splitext(splitted[1])[1]) > 0:
			return splitted[1]
		else:
			return rsearchFilename( splitted[0] )



# @todo improves stats (see test() for missing stats), and install/remove/test() prints the same stats => flags to select interesting stats)).# @todo renames into sbf-get and uses apt-get syntax.
# @todo creates a Statistics class
class PackagingSystem:

	# Statistics
	__numNewDirectories			= 0
	__numDeletedDirectories		= 0
	__numNotFoundDirectories	= 0
	__numNotEmptyDirectory		= 0

	__numNewFiles				= 0
	__numDeletedFiles			= 0
	__numNotFoundFiles			= 0
	__numOverrideFiles			= 0

	def __initializeStatistics( self ):
		self.__numNewDirectories		= 0
		self.__numDeletedDirectories	= 0
		self.__numNotFoundDirectories	= 0
		self.__numNotEmptyDirectory		= 0

		self.__numNewFiles				= 0
		self.__numDeletedFiles			= 0
		self.__numNotFoundFiles			= 0
		self.__numOverrideFiles			= 0

	def __printStatistics( self ):
		print
		print ( "Summary:" )

		if self.__numNewDirectories > 1:
			print (	"%i new directories," % self.__numNewDirectories ),
		else:
			print (	"%i new directory," % self.__numNewDirectories ),

		if self.__numNewFiles > 1:
			print ( "%i new files," % self.__numNewFiles ),
		else:
			print ( "%i new file," % self.__numNewFiles ),

		if self.__numOverrideFiles > 1:
			print ( "%i overridden files." % self.__numOverrideFiles )
		else:
			print ( "%i overridden file." % self.__numOverrideFiles )


		if self.__numDeletedDirectories > 1:
			print (	"%i deleted directories," % self.__numDeletedDirectories ),
		else:
			print (	"%i deleted directory," % self.__numDeletedDirectories ),

		if self.__numNotFoundDirectories > 1:
			print (	"%i not found directories," % self.__numNotFoundDirectories ),
		else:
			print (	"%i not found directory," % self.__numNotFoundDirectories ),

		if self.__numNotEmptyDirectory > 1:
			print (	"%i not empty directories," % self.__numNotEmptyDirectory ),
		else:
			print (	"%i not empty directory," % self.__numNotEmptyDirectory ),

		if self.__numDeletedFiles > 1:
			print ( "%i deleted files," % self.__numDeletedFiles ),
		else:
			print ( "%i deleted file," % self.__numDeletedFiles ),

		if self.__numNotFoundFiles > 1:
			print ( "%i not found files." % self.__numNotFoundFiles )
		else:
			print ( "%i not found file." % self.__numNotFoundFiles )



	def __init__( self, sbf, verbose = None ):
		self.__SCONS_BUILD_FRAMEWORK	= sbf.mySCONS_BUILD_FRAMEWORK

		if verbose != None:
			self.__verbose = verbose
		else:
			self.__verbose				= sbf.myEnv.GetOption('verbosity')

		self.__vcs						= sbf.myVcs

		self.__localPath				= sbf.myInstallDirectory
		self.__localExtPath				= sbf.myInstallExtPaths[0]
		self.__pakPaths 				= [ self.__mkPakGetDirectory(), join(self.__localPath, '..', 'sbfPak') ]
		self.__pakPaths.extend( sbf.myEnv['pakPaths'] )

		self.__myConfig							= sbf.myConfig
		self.__myPlatform						= sbf.myPlatform
		self.__myArch							= sbf.myArch
		self.__myCC								= sbf.myCC
		self.__myCCVersionNumber				= sbf.myCCVersionNumber
		self.__myCCVersion						= sbf.myCCVersion
		self.__clVersion						= sbf.myEnv['clVersion']
		self.__my_Platform_myArch_myCCVersion	= sbf.my_Platform_myArch_myCCVersion
		self.__myMSVSIDE						= sbf.myMSVSIDE
		self.__myMSVCVARS32						= sbf.myMSVCVARS32
		self.__myVCVARSALL						= sbf.myVCVARSALL
		self.__myMSVC							= sbf.myMSVC
		self.__myMSBuild						= sbf.myMSBuild

		self.__libSuffix						= sbf.myEnv['LIBSUFFIX']
		self.__shLibSuffix						= sbf.myEnv['SHLIBSUFFIX']

		# Tests existance of localExt directory
		if self.__verbose:	print
		if os.path.isdir( self.__localExtPath ) :
			if self.__verbose: print ("Found localExt in %s\n" % self.__localExtPath)
		else :
			if self.__verbose: print ("localExt not found in %s" % self.__localExtPath)
			createDirectory(self.__localExtPath)

		# Tests existance of pakPaths directory
		for path in self.__pakPaths :
			if os.path.isdir( path ) :
				if self.__verbose: print ("Found package repository in %s" % path)
			else :
				if self.__verbose: print ("WARNING: Package repository not found in %s" % path)
		if self.__verbose:	print

		# Creates localExt directory
		createDirectory( self.getLocalExtSbfPakDBPath() )

	# local or localExt ?
	def getDestinationDirectory( self, pakName ):
		"""Returns local directory for any runtime package or returns localExt directory for developer package."""
		if '-runtime' in pakName:
			return self.__localPath
		else:
			return self.__localExtPath

	# LocalExt
	def getLocalExtPath( self ):
		return self.__localExtPath

	def getLocalExtSbfPakDBPath( self ):
		return join( self.getLocalExtPath(), 'sbfPakDB' )

	def getLocalExtSbfPakDBTmpPath( self ):
		return join(self.getLocalExtSbfPakDBPath(), 'tmp' )


	# (M)a(K)e(D)ata(B)ase)
	def __mkdbGetDirectory( self ):
		return join( self.__SCONS_BUILD_FRAMEWORK, 'pak', 'mkdb' )


	def __mkPakGetDirectory( self ):
		return join( self.__SCONS_BUILD_FRAMEWORK, 'pak', 'var' )

	def __mkPakGetBuildDirectory( self ):
		return join( self.__mkPakGetDirectory(), 'build' )

	def __mkPakGetExtractionDirectory( self, pakDescriptor ):
		return join( self.__mkPakGetBuildDirectory(), pakDescriptor['name'] + pakDescriptor['version'] )

	def __getEnvironmentDict( self ):

		def SearchFiles( retVal, searchDirectory, pruneDirectoriesPatterns = [], allowedFilesRe = r".+" ):
			def _searchFiles( retVal, searchDirectory, pruneDirectoriesPatterns = [], allowedFilesRe = r".+" ):
				import src.sbfFiles
				src.sbfFiles.searchFiles( searchDirectory, retVal, pruneDirectoriesPatterns, allowedFilesRe )
			return lambda : _searchFiles( retVal, searchDirectory, pruneDirectoriesPatterns, allowedFilesRe )

		def SearchVcxproj( retVal, searchDirectory, pruneDirectoriesPatterns = [], allowedFilesRe = r".*[.]vcxproj$" ):
			return SearchFiles( retVal, searchDirectory, pruneDirectoriesPatterns, allowedFilesRe )


		def RequiredProgram( executableName ):
			from src.sbfTools import locateProgram
			location = locateProgram(executableName)
			if location:
				print ( 'Found {} in {}.'.format( executableName, location ) )
				return location
			else:
				print( 'ERROR: Unable to find {} in PATH'.format(executableName) )
				exit(1)


		def MakeDirectory( newDirectory ):
			def makeDirectory( newDirectory ):
				import os
				if not os.path.exists(newDirectory):
					os.mkdir( newDirectory )
					if os.path.isabs(newDirectory):
						print ('Creating directory {}'.format(newDirectory))
					else:
						print ('Creating directory {}'.format(join(os.getcwd(), newDirectory)))
			return lambda : makeDirectory(newDirectory)

		def RemoveDirectory( directory ):
			def removeDirectory( directory ):
				import os
				if os.path.exists(directory):
					os.rmdir( directory )
					if os.path.isabs(directory):
						print ('Removing directory {}'.format(directory))
					else:
						print ('Removing directory {}'.format(join(os.getcwd(), directory)))
			return lambda : removeDirectory(directory)

		def ChangeDirectory( newDirectory ):
			def changeDirectory( newDirectory ):
				import os
				os.chdir( newDirectory )
				print ('Entering directory {}'.format(os.getcwd()))
			return lambda : changeDirectory(newDirectory)

		def RemoveFile( file ):
			def removeFile( file ):
				import os
				if os.path.exists(file):
					os.remove( file )
					if os.path.isabs(file):
						print ('Removing file {}'.format(file))
					else:
						print ('Removing file {}'.format(join(os.getcwd(), file)))
			return lambda : removeFile(file)


		def CreateSConsBuildFrameworkProject( projectName, type, version, includeFiles, sourceFiles ):
			return lambda : createSConsBuildFrameworkProject( projectName, type, version, includeFiles, sourceFiles )

		def BuildDebugAndReleaseUsingSConsBuildFramework( path, CCVersion, arch ):
			return lambda : buildDebugAndReleaseUsingSConsBuildFramework( path, CCVersion, arch )


		def GetCMakeInitialCacheCodeToAppendValue( variableName, valueToAppend ):
			"""Retrieve code for CMakeInitialCache.txt to append a value at the end of an existing variable
				@param variableName		name of the variable to customize
				@param valueToAppend	content to append to CMAKE_variableName"""

			str = """message("Input: CMAKE_{name}=${{CMAKE_{name}}}")

if (CMAKE_{name})
	message("Customizing CMAKE_{name}")

	# add new flags
	set (FLAGS "${{CMAKE_{name}}} {value} ")

	set(CMAKE_{name} "${{FLAGS}}" CACHE STRING "" FORCE)
	message("Output:CMAKE_{name}=${{CMAKE_{name}}}")
else()
	message("Don't customize CMAKE_{name}")
endif()
"""
			return str.format( name=variableName, value = valueToAppend )

		def CreateCMakeInitialCache( directory, contents ):
			"""	@param directory		path where CMakeInitialCache.txt file would be created
				@param contents			contents of the CMakeInitialCache.txt file to create"""
			def _createCMakeInitialCacheFile( directory, contents ):
				with open( join(directory, 'CMakeInitialCache.txt'), 'w' ) as f:
					f.write(contents)
			return lambda : _createCMakeInitialCacheFile(directory, contents)


		def _filePatcher( file, resubs, flags = 0):
			"""	@param file		the filename to patch
				@param resubs	a list of [(pattern, repl),...] see re.sub(pattern, repl,...)
				@param flags	see re flags parameter
			"""
			import re
			with open( file, 'r+' ) as fd:
				# Read file
				lines = fd.readlines()

				# Patch the file in memory
				for(i, line) in enumerate(lines):
					for resub in resubs:
						(pattern, repl ) = resub
						line = re.sub( pattern, repl, line, flags=flags )
					lines[i] = line

				# Write file
				fd.seek(0)
				fd.truncate()
				fd.writelines(lines)

		def _patcher( fileOrFileList, resubs, flags = 0):
			if isinstance(fileOrFileList, str):
				_filePatcher(fileOrFileList, resubs, flags)
			else:
				for file in fileOrFileList:
					_filePatcher(file, resubs, flags)

		def _filePatcherMultiline( file, resubs, flags = 0):
			"""	@param file		the filename to patch
				@param resubs	a list of [(pattern, repl),...] see re.sub(pattern, repl,...)
				@param flags	see re flags parameter
			"""
			import re
			with open( file, 'r+' ) as fd:
				# Read file
				lines = fd.read()

				# Patch the file in memory
				for resub in resubs:
					(pattern, repl ) = resub
					lines = re.sub( pattern, repl, lines, flags=flags )

				# Write file
				fd.seek(0)
				fd.write(lines)

		def _patcherMultiline( fileOrFileList, resubs, flags = 0):
			if isinstance(fileOrFileList, str):
				_filePatcherMultiline(fileOrFileList, resubs, flags)
			else:
				for file in fileOrFileList:
					_filePatcherMultiline(file, resubs, flags)

		def Patcher( fileOrFileList, resubs, flags = 0 ):
			return lambda : _patcher(fileOrFileList, resubs, flags)

		def PatcherMultiline( fileOrFileList, resubs, flags = 0 ):
			return lambda : _patcherMultiline(fileOrFileList, resubs, flags)

		def ChangeContentOfAnXMLElement(fileOrFileList, tag, oldContent, newContent ):
			"""@brief Change content of an XML element for the given file(s)
				for example: <tag>oldContent</tag> transformed into <tag>newContent</tag>
				@param oldContent	specify the content to transform, or None to replace the content for the desired elements anyway.
				@param newContent	the new content to set. \\2 to add the oldContent"""
			if not oldContent:
				oldContent = '.*'
			return lambda : _patcherMultiline(fileOrFileList, [('^(.*\<{tag}\>)({oldContent})(\</{tag}\>.*)$'.format(tag=tag, oldContent=oldContent), '\\1{}\\3'.format(newContent))])


		def RemoveProjectFromSolution( file, projectName ):
			return lambda : _patcherMultiline(file, [('Project.*?{}(?:.*\n)+?EndProject'.format(projectName), '')], 0 )

		def ChangeTargetName( VCXProjFileOrFileList, oldName, newName ):
			return lambda : _patcher(VCXProjFileOrFileList, [	#('^(.*\$\(OutDir\)){}(\..*)$'.format(oldName), '\\1{}\\2'.format(newName)),
													('^(.*TargetName Condition.*){}(.*TargetName.*)$'.format(oldName), '\\1{}\\2'.format(newName)),
													('^(.*ImportLibrary.*){}(\.lib.*ImportLibrary.*)$'.format(oldName), '\\1{}\\2'.format(newName)),
													('^(.*ProgramDataBaseFileName.*){}(\.pdb.*ProgramDataBaseFileName.*)$'.format(oldName), '\\1{}\\2'.format(newName)),
													('^(.*ProgramDataBaseFile.*){}(\.pdb.*ProgramDataBaseFile.*)$'.format(oldName), '\\1{}\\2'.format(newName))
													] )

		def SetPlatformToolset( VCXProjFileOrFileList, CCVersionNumber ):
			"""<PlatformToolset>v110</PlatformToolset> => <PlatformToolset>vXYZ</PlatformToolset> with XYZ compute from CCVersionNumber"""
			toPlatformToolset = { 10 : 'v100', 11 : 'v110', 12 : 'v120' }
			if CCVersionNumber not in toPlatformToolset:
				print ('CCVersionNumber {} given to SetPlatformToolset() is not yet supported.'.format(CCVersionNumber))
				exit(1)
			return lambda : _patcher(VCXProjFileOrFileList, [('^(.*\<PlatformToolset\>).*(\</PlatformToolset\>)$', '\\1{}\\2'.format(toPlatformToolset[CCVersionNumber]))])

		def AddMultiProcessorCompilation( VCXProjFileOrFileList ):
			return lambda : _patcher(VCXProjFileOrFileList, [('^(.*\<ClCompile\>.*)$', '\\1\n<MultiProcessorCompilation>true</MultiProcessorCompilation>')])

		def AddPreprocessorDefinitions( VCXProjFileOrFileList, definesToAdd ):
			"""@param definesToAdd		DEFINE1;DEFINE2"""
			return lambda : _patcher(VCXProjFileOrFileList, [('^(.*\<PreprocessorDefinitions\>)(.*)(\</PreprocessorDefinitions\>)$','\\1{};\\2\\3'.format(definesToAdd))])

		def ChangeLinkVersion( VCXProjFileOrFileList, oldVersion, newVersion ):
			"""<Version>oldVersion</Version> => <Version>newVersion</Version>"""
			return lambda : _patcher(VCXProjFileOrFileList, [('^(.*\<Version\>){oldVersion}(\</Version\>)(.*)$'.format(oldVersion=oldVersion), '\\g<1>{newVersion}\\g<2>\\g<3>'.format(newVersion=newVersion))] )


		def ConfigureVisualStudioVersion( CCVersionNumber ):
			os.environ['VisualStudioVersion'] = str(int(CCVersionNumber)) + '.0'

		def GetMSBuildCommand( execPath, sln, targets = 'build', config = 'Release', logFile = None, maxcpucount = 1, platform = 'Win32', msbuild=self.__myMSBuild ):
			cmd = 'cd {execPath} && \"{msbuild}\" /nologo \"{sln}\" '.format( execPath=execPath, msbuild=msbuild, sln=sln )
			if len(targets) > 0:
				cmd += ' /t:{targets} '.format( targets=targets )

			cmd += ' /p:Configuration={config} /p:Platform={platform} '.format(config=config, platform=platform)
	
			cmd += '/consoleloggerparameters:Summary;Verbosity=minimal '
			#cmd += '/consoleloggerparameters:Summary;Verbosity=normal '

			if logFile:
				cmd += '/fileLogger /fileloggerparameters:logfile={logFile};Verbosity=minimal;Append '.format( logFile )

			cmd += '/maxcpucount:{maxcpucount} '.format(maxcpucount=maxcpucount)

			#cmd += ' /tv:12.0 '
			#cmd += ' /p:BuildProjectReferences=false '
			#<ImageHasSafeExceptionHandlers>false</ImageHasSafeExceptionHandlers>

			return cmd

		envDict	= {	'cpuCount'					: multiprocessing.cpu_count(),
					'config'					: self.__myConfig,
					'platform'					: self.__myPlatform,
					'arch'						: self.__myArch,
					'CC'						: self.__myCC,
					'CCVersionNumber'			: self.__myCCVersionNumber,
					'CCVersion'					: self.__myCCVersion,
					'clVersion'					: self.__clVersion,
					'platform_arch_ccVersion'	: self.__my_Platform_myArch_myCCVersion[1:],
					'libSuffix'					: self.__libSuffix,
					'shLibSuffix'				: self.__shLibSuffix,
					'MSVSIDE'					: self.__myMSVSIDE,
					'MSVCVARS32'				: self.__myMSVCVARS32,
					'VCVARSALL'					: self.__myVCVARSALL,
					'MSVC'						: self.__myMSVC,
					'MSBuild'					: self.__myMSBuild,

					'UseRepository'				: UseRepository,
					'execCmdInVCCmdPrompt'		: getLambdaForExecuteCommandInVCCommandPrompt(self.__myVCVARSALL, self.__myArch),

					'buildDirectory'	: self.__mkPakGetBuildDirectory(),
					'localDirectory'	: self.__localPath,
					'localExtDirectory' : self.__localExtPath,

					'GlobRegEx'			: GlobRegEx,
					'SearchFiles'		: SearchFiles,
					'SearchVcxproj'		: SearchVcxproj,

					'RequiredProgram'	: RequiredProgram,

					'MakeDirectory'					: MakeDirectory,
					'RemoveDirectory'				: RemoveDirectory,
					'ChangeDirectory'				: ChangeDirectory,
					'RemoveFile'					: RemoveFile,

					'CreateSConsBuildFrameworkProject'				: CreateSConsBuildFrameworkProject,
					'BuildDebugAndReleaseUsingSConsBuildFramework'	: BuildDebugAndReleaseUsingSConsBuildFramework,

					'GetCMakeInitialCacheCodeToAppendValue'			: GetCMakeInitialCacheCodeToAppendValue,
					'CreateCMakeInitialCache'						: CreateCMakeInitialCache,

					'GetAutoconfBuildingCommands'					: sbfAutoconf.getAutoconfBuildingCommands,

					'Patcher'						: Patcher,
					'PatcherMultiline'				: PatcherMultiline,
					'ChangeContentOfAnXMLElement'	: ChangeContentOfAnXMLElement,
					'MSVC'							: { 'RemoveProjectFromSolution'		: RemoveProjectFromSolution,
														'ChangeTargetName'				: ChangeTargetName,
														'SetPlatformToolset'			: SetPlatformToolset,
														'AddMultiProcessorCompilation'	: AddMultiProcessorCompilation,
														'AddPreprocessorDefinitions'	: AddPreprocessorDefinitions,
														'ChangeLinkVersion'				: ChangeLinkVersion
														 },
					'ConfigureVisualStudioVersion'	: ConfigureVisualStudioVersion,
					'GetMSBuildCommand'				: GetMSBuildCommand
					}
		return envDict


	def mkdbListPackage( self, pattern = '' ):
		"""@return the list of files (without extension) containing descriptor of package found in mkdb using the given pattern (a glob)
		For example ['boost', 'sdl']
		"""
		db = glob.glob( join( self.__mkdbGetDirectory(), '{}.py'.format(pattern) ) )
		return [os.path.basename(elt)[:-3] for elt in db]


	def mkdbGetDescriptor( self, pakName ):
		"""Retrieves the dictionary named 'descriptor' from the mkdb database for the desired package"""
		localsFileDict = self.__getEnvironmentDict()
		execfile( join(self.__mkdbGetDirectory(), pakName), globals(), localsFileDict )
		return localsFileDict['descriptor']


	def mkPak( self, pakName ):
		"""	@briefRetrieves sources of a package, build them and creates the package
			@remark pakName parameter have to be specified without .py extension"""
		# Adds .py to pakName
		pakName = '{}.py'.format(pakName)

		#
		pakDescriptor = self.mkdbGetDescriptor(pakName)

		if ('name' not in pakDescriptor) or ('version' not in pakDescriptor):
			print ("Package description without 'name' and/or 'version'")
			return

		# Creates the sandbox (i.e. private directory)
		createDirectory( self.__mkPakGetDirectory() )
		createDirectory( join(self.__mkPakGetDirectory(), 'cache' ) )
		createDirectory( self.__mkPakGetBuildDirectory() )

		# Moves to sandbox
		backupCWD = os.getcwd()
		os.chdir( join(self.__mkPakGetDirectory() ) )

		# Computes directories
		extractionDirectory = self.__mkPakGetExtractionDirectory( pakDescriptor )
		fullVersion = pakDescriptor['version'] + pakDescriptor.get( 'buildVersion', '' )
		pakDirectory = pakDescriptor['name'] + fullVersion + self.__my_Platform_myArch_myCCVersion + '/' # '/' is needed to specify directory to copy()
		runtimePakDirectory = pakDescriptor['name'] + '-runtime' + fullVersion + self.__my_Platform_myArch_myCCVersion + '/' # '/' is needed to specify directory to copy()
		runtimePakDirectoryR = pakDescriptor['name'] + '-runtime-release' + fullVersion + self.__my_Platform_myArch_myCCVersion + '/' # '/' is needed to specify directory to copy()
		runtimePakDirectoryD = pakDescriptor['name'] + '-runtime-debug' + fullVersion + self.__my_Platform_myArch_myCCVersion + '/' # '/' is needed to specify directory to copy()

		# Removes old directories
# DEBUG
		removeDirectoryTree( extractionDirectory )
		removeDirectoryTree( pakDirectory )
		removeDirectoryTree( runtimePakDirectory )
		removeDirectoryTree( runtimePakDirectoryR )
		removeDirectoryTree( runtimePakDirectoryD )
		print

		# URLS (download and extract)
		# SVNURL (export svn)
		if 'svnUrl' in pakDescriptor:
			svnUrl = pakDescriptor['svnUrl']
			project = pakDescriptor['name']
			(url, rev) = splitSvnUrl( svnUrl, project )
			if rev:
				print ( '* Retrieves {0} from {1} at revision {2}'.format( project, url, rev ) )
				self.__vcs._export( url, join(extractionDirectory, project), rev )
			else:
				print ( '* Retrieves {0} from {1}'.format( project, url ) )
				self.__vcs._export( url, join(extractionDirectory, project) )
			print


		# URLS
		import urllib
		import urlparse
# DEBUG
#		for url in []:
		for entry in pakDescriptor.get('urls', []):
			if isinstance(entry, tuple):
				(url, extractionSubDirectory ) = entry
			else:
				url = entry
				extractionSubDirectory = ''

			# Computes filename
			filename = rsearchFilename( urlparse.urlparse(url).path )

			# in cache ?
			filenameInCache = join('cache', filename)
#			if not exists( filenameInCache ):
			if True:
				# not in cache
				if '$SRCPAKPATH' in url:
					# Replaces $SRCPAKPATH using option 'pakPaths' of SConsBuildFramework
					for pakPath in self.__pakPaths[2:]:
						newUrl = url.replace('$SRCPAKPATH', join(pakPath, 'src'), 1)
						print ('Is {} an existing path ?'.format(newUrl))
						if exists( newUrl ):
							copyFile( newUrl, filenameInCache, True )
							break
						# else continue
					else:
						print('Unable to found file {}'.format(filename))
						exit(1)
				else:
					print ( '* Retrieving %s from %s' % (filename, urlparse.urlparse(url).hostname ) )
					urllib.urlretrieve(url, filename= filenameInCache, reporthook=reporthook_urlretrieve)
					print ( 'Done.' + ' '*16 )
			else:
				# already available in cache
				print ('* %s already downloaded.' % filename)
				print

			# Extracts
			extractionDirectory = join(extractionDirectory, extractionSubDirectory)
			print ( '* Extracting {} in {}...'.format( filename, extractionDirectory ) )
			retVal = extractArchive( join('cache', filename), extractionDirectory, self.__verbose )
			if not retVal:
				print ('Error during extraction of {}'.format(filename))
				return
			else:
				retVal = extractAllTarFiles( extractionDirectory, self.__verbose )
				if not retVal:
					print ('Error during extraction of {}'.format(filename))
					return

		# BUILDS
		import datetime
		import subprocess
		import sys
		rootBuildDir = pakDescriptor.get('rootBuildDir', '')
		builds = pakDescriptor.get('builds', [])
		if len(builds)>0:
			# Moves to extraction directory
			buildBackupCWD = os.getcwd()

			os.chdir( extractionDirectory )
			if len(rootBuildDir) > 0:
				os.chdir( rootBuildDir )
				print ('* Entering directory {}\n'.format(rootBuildDir))

			# Executes commands
			print ( '* Building stage...' )
# @todo improves output of returned values
			startTime = datetime.datetime.now()
			for (i, build) in enumerate(builds):
				print ( ' Step {0}: {1}'.format(i+1, build) )
				print ( ' ----------------------------------------' )
				if type(build) == types.FunctionType:
					retVal = build()
					if retVal:
						print >>sys.stderr, "Execution {0} failed returning {1}:".format( build, retVal )
						exit(1)
				else:
					try:
						retcode = subprocess.call( build, shell=True )
						if retcode < 0:
							print >>sys.stderr, "Child was terminated by signal", -retcode
						else:
							print >>sys.stderr, "Child returned", retcode
					except OSError, e:
						print >>sys.stderr, "Execution failed:", e
						exit(1)
				print
			endTime = datetime.datetime.now()
			timeSpent = endTime-startTime
			print ( 'Total build time : {0}m {1}s\n'.format( timeSpent.seconds / 60, timeSpent.seconds % 60 ) )

			# Restores old current working directory
			os.chdir( buildBackupCWD )

		# CREATES PAK
		sourceDir = join( extractionDirectory, pakDescriptor.get('rootDir','') )
		if not exists( sourceDir ):
			print ('{} does not exist'.format( sourceDir) )
			exit(1)
		else:
			print ('* Entering directory {}\n'.format(sourceDir))

		print ('* Creating package {}'.format(pakDirectory[:-1]) )

		# Creates directories
		createDirectory( pakDirectory )
		#print

		# Copies license files
		for i, licenseFile in enumerate(pakDescriptor.get('license', [])):
			if len(pakDescriptor['license']) > 1:
				prefix = i
			else:
				prefix = ''
			copy(	licenseFile,
					join( 'license', '{0}license.{1}{2}.txt'.format( prefix, pakDescriptor['name'], pakDescriptor['version']) ),
					sourceDir, pakDirectory )
		#print

		# Copies include files
		for include in pakDescriptor.get('include', []):
			if isinstance(include, tuple):
				copy( include[0], join( 'include', include[1] ), sourceDir, pakDirectory )
			else:
				copy( include, 'include/', sourceDir, pakDirectory )
		#else:
		#	print

		# Copies lib files
		for lib in pakDescriptor.get('lib', []):
			if isinstance(lib, tuple):
				copy( lib[0], join( 'lib', lib[1] ), sourceDir, pakDirectory )
			else:
				copy( lib, 'lib/', sourceDir, pakDirectory )
		#else:
		#	print

		# Copies custom files
		for elt in pakDescriptor.get('custom', []):
			if not isinstance(elt, tuple):
				elt = (elt,elt)
			copy( elt[0], elt[1], sourceDir, pakDirectory )
		#else:
		#	print

		# Creates archive
		pakDirectory = pakDirectory[:-1] # removes the last character '/'
		pakFile = '{}.{}'.format( pakDirectory, defaultArchiveFormat )
		if exists(pakFile):	removeFile( pakFile )
		print ( ' => Creating archive {}\n'.format(pakFile) )
		retVal = createArchive(pakFile, pakDirectory, self.__verbose)
		if not retVal:
			return


		# CREATE A RUNTIME PACKAGE
		def createRuntimePackage( pakDescriptor, sourceDir, runtimePakDirectory, binEntry, runtimeCustomEntry ):
		#if (binEntry in pakDescriptor) or (runtimeCustomEntry in pakDescriptor):
			print ('* Creating package {}'.format(runtimePakDirectory[:-1]) )

			# Creates directories
			createDirectory( runtimePakDirectory )
			print

			# Copies bin files
			for bin in pakDescriptor.get(binEntry, []):
				if isinstance(bin , tuple):
					copy( bin[0], join( 'bin', bin[1] ), sourceDir, runtimePakDirectory )
				else:
					copy( bin, 'bin/', sourceDir, runtimePakDirectory )
			#else:
			#	print

			# Copies custom files
			for elt in pakDescriptor.get(runtimeCustomEntry, []):
				if not isinstance(elt, tuple):
					elt = (elt,elt)
				copy( elt[0], elt[1], sourceDir, runtimePakDirectory )
			#else:
			#	print

			# Creates zip
			runtimePakDirectory = runtimePakDirectory[:-1] # removes the last character '/'
			pakFile = '{}.{}'.format( runtimePakDirectory, defaultArchiveFormat )
			if exists(pakFile):	removeFile( pakFile )
			print ( ' => Creating archive {}\n'.format(pakFile) )
			retVal = createArchive(pakFile, runtimePakDirectory, self.__verbose)
			if not retVal:
				return

		# RUNTIME PACKAGE
		createRuntimePackage( pakDescriptor, sourceDir, runtimePakDirectory, 'bin', 'runtimeCustom' )

		# RUNTIME PACKAGE (in release)
		createRuntimePackage( pakDescriptor, sourceDir, runtimePakDirectoryR, 'binR', 'runtimeCustomR' )

		# RUNTIME PACKAGE (in debug)
		createRuntimePackage( pakDescriptor, sourceDir, runtimePakDirectoryD, 'binD', 'runtimeCustomD' )

		# Restores old current working directory
		os.chdir( backupCWD )



	### PAK INFO ###
	def __printPackageNameAndVersion__( self, packageName ):
		oPakInfo = {}
		oRelDirectories = []
		oRelFiles = []
		self.loadPackageInfo( packageName, oPakInfo, oRelDirectories, oRelFiles )
		print oPakInfo['name'].ljust(34), oPakInfo['version'].ljust(10)

	def savePackageInfo( self, pakInfo, relDirectories, relFiles ):
		sbfpakDir = self.getLocalExtSbfPakDBPath()
		pathInfoFile = join(sbfpakDir, pakInfo['name'] + '.info')

		with open( pathInfoFile, 'wb' ) as output:
			cPickle.dump( pakInfo, output )
			cPickle.dump( relDirectories, output )
			cPickle.dump( relFiles, output )

	def loadPackageInfo( self, pakName, oPakInfo, oRelDirectories = [], oRelFiles = [] ):
		"""@pre isInstalled( pakName )"""
		assert( self.isInstalled(pakName) )

		sbfpakDir = self.getLocalExtSbfPakDBPath()
		pathInfoFile = join(sbfpakDir, pakName + '.info')

		with open( pathInfoFile, 'rb' ) as input:
			oPakInfo.update( cPickle.load(input) )
			oRelDirectories.extend( cPickle.load(input) )
			oRelFiles.extend( cPickle.load(input) )


	def isInstalled( self, packageName ):
		return exists( join(self.getLocalExtSbfPakDBPath(), packageName + '.info') )


	def listInstalled( self, pattern = '', enablePrint = False ):
		"""	@param pattern		glob(pattern)
			@return the list of installed packages filtered by pattern."""
		files = glob.glob( join(self.getLocalExtSbfPakDBPath(), '{}.info'.format(pattern)) )
		files = [splitext(basename(file))[0] for file in sorted(files)]

		for file in files:
			if enablePrint: self.__printPackageNameAndVersion__(file)

		return files


	### Availability/retrieving of packages ###
	def locatePackage( self, pakName ):
		"""@return the path where pakName has been found, otherwise None"""
		for path in self.__pakPaths :
			pathPakName = join( path, pakName )
			if os.path.isfile(pathPakName):
				return pathPakName


	def isAvailable( self, pakName ):
		"""@return True if pakName is available, otherwse False"""
		pathPakName = self.locatePackage(pakName)
		return pathPakName and len(pathPakName)>0


	# @todo move implicit filtering (i.e. filter = self.__my_Platform_myArch_myCCVersion in class sbfPakCmd)
	def listAvailable( self, pattern = '', enablePrint = True, automaticFiltering = True ):
		"""	@param pattern				glob(pattern)
			@param automaticFiltering	True to replace automatically pattern by {}{}.{}.format(pattern, __my_Platform_myArch_myCCVersion, extension), False to use pattern directly
			@return list of filenames corresponding to package filter by pattern
		"""
		filenames = set()

		if automaticFiltering:
			filter = self.__my_Platform_myArch_myCCVersion
		else:
			filter = ''

		for pakPath in self.__pakPaths:
			elements = []
			for extension in supportedArchiveFormats:
				elements += glob.glob( join(pakPath, '{}{}.{}'.format(pattern, filter, extension)) )
				# Don't differentiate Visual C++ edition (express, pro, community...)
				if automaticFiltering and self.__myPlatform == 'win' and self.__myCC == 'cl':
					if filter.endswith('Exp'):
						elements += glob.glob( join(pakPath, '{}{}.{}'.format(pattern, filter.replace('Exp', '', 1), extension)) )
					else:
						elements += glob.glob( join(pakPath, '{}{}.{}'.format(pattern, filter + 'Exp', extension)) )

			sortedElements = sorted( elements )
			if enablePrint:
				if len(sortedElements)>0:
					print ("\nAvailable packages in {} :".format(pakPath))
			for element in sortedElements:
				filename = basename(element)
				pakInfo = splitPackageName(filename)
				if not pakInfo:		continue	# unable to split package name, so skip to next element

				filenameWithoutExt = splitext(filename)[0]
				if automaticFiltering:
					splitted = filenameWithoutExt.split( filter, 1 )
					if len(splitted) == 1:
					  # The current platform and compiler version not found in package filename, so don't print it
					  continue
				if enablePrint:	print pakInfo['name'].ljust(34), pakInfo['version'].ljust(10)
				filenames.add(filename)

		return list(filenames)



	def listAvailablePackageName(self, packageNameFilter):
		"""	@param packageNameFilter		glob(packageNameFilter)
			@return the list of available packages name. Example ['boost', 'boost-runtime', 'boost-runtime-debug', 'boost-runtime-release', ...]
		"""
		filenames = self.listAvailable( packageNameFilter, False )
		return [ splitPackageName(filename)['name'] for filename in filenames ]

	def getPackageFilename(self, packageName ):
		"""	@return the name of file corresponding to the given packageName, otherwise an empty string.
			Example: _getPackageFilename('boost') could returned 'boost1-56-0_posix_x86-32_gcc4-8.tar.bz2'"""
		filenames = self.listAvailable( packageName + '*', False )
		for filename in filenames:
			pakInfo = splitPackageName(filename)
			if pakInfo['name'] == packageName:
				return filename
		return ''


	def getLocalPackage( self, pakName, localDir ):
		"""	@brief Search package pakName in different repositories and copy it in localDir (if needed).
			@return (the path to the copy of pakName, pakName)

			@remarks On Windows platform with compiler cl.exe from Microsoft, when pakName is not found, try to found package name with/without (depending of the initial lookup) 'Exp' postfix.
		"""

		# Computes pakNames
		if self.__myPlatform == 'win':
			if pakName.rfind('Exp.') != -1:		# package name contains Exp (i.e. express version of Visual C++)
				secondPakName = pakName.replace('Exp.', '.', 1) # remove Exp
			else:
				splitPakName = pakName.rsplit('.', 1)
				secondPakName = '{}Exp.{}'.format( splitPakName[0], splitPakName[1] )	# add Exp
			pakNames = [pakName, secondPakName]
		else:
			pakNames = [pakName]

		# Search package
		for currentPakName in pakNames:
			pathPakName = self.locatePackage( currentPakName )
			if pathPakName:
				localPakName = join( localDir, currentPakName )
				copyFile( pathPakName, localPakName, self.__verbose ) # @todo error proof
				return (localPakName, currentPakName)

		print ("Unable to find package {}".format(pakNames) )
		return (None, None)

	### Package actions ###
	def install( self, packageFilename, forced = False ):
		"""	@brief install package named pakName
			@param packageFilename		name of the file containing the package to install (example: boost1-56-0_posix_x86-32_gcc4-8.tar.bz2)
			@param forced				True to force the installation even if already installed

			@return False if an error occurs during installation, False otherwise
		"""

		pakInfo = splitPackageName( packageFilename )
		if not pakInfo:
			return False

		if (not forced) and self.isInstalled( pakInfo['name'] ):
			print ( "Package {} already installed.".format(pakInfo['name']) )
			return False

		# Retrieves paths to several directories
		sbfpakDir = self.getLocalExtSbfPakDBPath()

		# Retrieves package pakName
		(pathPackageFilename, packageFilename) = self.getLocalPackage( packageFilename, sbfpakDir )
		if not packageFilename:
			return False
		else:
			pakInfo = splitPackageName( packageFilename )

		if self.__verbose:
			print ( "\nInstalling package {} version {} using {}...".format( pakInfo['name'], pakInfo['version'], pathPackageFilename ) )
			print ('\nDetails :')
		else:
			print ( "\nInstalling package {} version {}...".format( pakInfo['name'], pakInfo['version'] ) )

		# Computes destination directory (local or localExt)
		destinationDir = self.getDestinationDirectory( packageFilename )		

		# Extracts pak		
		if pakInfo['extension'] == 'zip':
			# Zip packages have been deprecated.
			tmpDir = self.getLocalExtSbfPakDBTmpPath()
			removeDirectoryTree( tmpDir, self.__verbose )
			createDirectory( tmpDir, self.__verbose )

			retVal = extractArchive( pathPackageFilename, tmpDir, self.__verbose )
			if not retVal:
				print ('Error during extraction of {}'.format(pakInfo['name']))
				return False
			if self.__verbose:	print

			# Collects all files and directories
			absFiles = []
			absDirectories = []
			searchAllFilesAndDirectories( tmpDir, absFiles, absDirectories, False )
			# Converts files and directories to be relative to tmp/localExt_platform_cc
			relFiles = [convertPathAbsToRel(tmpDir, file) for file in absFiles]
			relDirectories = [convertPathAbsToRel(tmpDir, dir) for dir in absDirectories]
			relFiles = removePathHead( relFiles )		# Removes the root directory of the archive (example: boost1-56-0_posix_x86-32_gcc4-8)
			relDirectories = removePathHead( relDirectories )
			relDirectories = sorted(relDirectories, key=lambda value: value.count(os.sep), reverse=True) # sort directories using depth criterion

			# Copies the tree
			dirs = os.listdir(tmpDir)
			if len(dirs) == 0:
				pass
			elif len(dirs) == 1:
				cwdBAK = os.getcwd()
				os.chdir( join(tmpDir, dirs[0]) )
				copy( '.', destinationDir + '/', verbose = self.__verbose )
				os.chdir(cwdBAK)
			else:
				print("Zip package have to contain only one root directory.")
				return False

			# Saves pak info
			self.savePackageInfo( pakInfo, relDirectories, relFiles )

			# Cleans
			removeDirectoryTree( tmpDir, self.__verbose )
		else: # not a zip archive
			retVal = extractArchive( pathPackageFilename, destinationDir, self.__verbose )
			if not retVal:
				print ('Error during extraction of {}'.format(pakInfo['name']))
				return False
			if self.__verbose:	print

			# Collects informations about all files and directories
			relFiles = []
			relDirectories = []
			getFilesAndDirectories( pathPackageFilename, relFiles, relDirectories )
			relDirectories = sorted(relDirectories, key=lambda value: value.count(os.sep), reverse=True) # sort directories using depth criterion

			# Saves pak info
			self.savePackageInfo( pakInfo, relDirectories, relFiles )

		print ('Done.')
		return True


	def remove( self, packageName ):
		"""@pre isInstalled(packageName)"""

		if not self.isInstalled( packageName ):
			print ( "Package {} is not installed.".format(packageName) )
			return

		# Load package info
		oPakInfo = {}
		oRelDirectories = []
		oRelFiles = []
		self.loadPackageInfo( packageName, oPakInfo, oRelDirectories, oRelFiles )
		packageFilename = joinPackageName( oPakInfo )

		# for debugging
		#print oPakInfo['name'].ljust(30), oPakInfo['version'].ljust(10)#, oPakInfo['platform'], oPakInfo['cc'], len(oRelFiles)
		#print packageFilename

		# Retrieves paths to several directories
		sbfpakDir = self.getLocalExtSbfPakDBPath()

		if self.__verbose:
			print ( "\nRemoving package {} version {}...\nDetails :".format( packageName, oPakInfo['version'] ) )
		else:
			print ( "\nRemoving package {} version {}...".format( packageName, oPakInfo['version'] ) )

		# Initializes statistics
		self.__initializeStatistics()

		# Computes destination directory (local or localExt)
		destinationDir = self.getDestinationDirectory( packageFilename )

		# Removes files
		if self.__verbose:	print ('\nRemoving files...')
		for relFile in oRelFiles:
			absFile = join( destinationDir, relFile )
			if exists(absFile):
				os.remove( absFile )
				self.__numDeletedFiles += 1
				if self.__verbose:	print ( 'Removing {}'.format(absFile) )
			else:
				self.__numNotFoundFiles += 1
				if self.__verbose:	print ( '{} already removed.'.format(absFile) )

		# Removes directories
		if self.__verbose:	print ('\nRemoving directories...')
		for relDir in oRelDirectories:
			absDir = join( destinationDir, relDir )
			if exists( absDir ):
				if len( os.listdir(absDir) ) == 0:
					os.rmdir( absDir )
					self.__numDeletedDirectories += 1
					if self.__verbose:	print ( 'Removing {}'.format(absDir) )
				else:
					self.__numNotEmptyDirectory += 1
					if self.__verbose:	print ( 'Directory {} not empty.'.format(absDir) )
			else:
				self.__numNotFoundDirectories += 1
				if self.__verbose:	print ( '{} already removed.'.format(absDir) )

		# Removes package archive and pak info
		os.remove( join(sbfpakDir, packageFilename) )
		os.remove( join(sbfpakDir, packageName + '.info') )

		# Prints statistics
		if self.__verbose:
			print ('Done.'),
			self.__printStatistics()
		else:
			print ('Done.')


	# def test( self, pathFilename ):

		# # Opens package
		# zip = zipfile.ZipFile( pathFilename )

		# # Initializes statistics
		# self.__initializeStatistics()
		# differentFile	= 0
		# identicalFile	= 0

		# #
		# print
		# print ( "Tests package using %s" % pathFilename )
		# print
		# print ('Details :')

		# for name in zip.namelist() :
			# normalizeName			= os.path.normpath( name )
			# normalizeNameSplitted	= normalizeName.split( os.sep )

			# normalizeNameTruncated	= None
			# if len(normalizeNameSplitted) > 1 :
				# normalizeNameTruncated = normalizeName.replace( normalizeNameSplitted[0] + os.sep, '' )
			# else :
				# continue

			# if not name.endswith('/') :
				# # element is a file
				# fileInLocalExt = join( self.__localExtPath, normalizeNameTruncated )

				# # Tests directory
				# if not os.path.lexists(os.path.dirname(fileInLocalExt)):
				  # print ( 'Missing directory %s' % os.path.dirname(fileInLocalExt) )
				  # self.__numNotFoundDirectories += 1

				# if os.path.isfile( fileInLocalExt ):
				  # # Tests contents of the file
				  # referenceContent = zip.read(name)
				  # installedContent = ''
				  # with open( fileInLocalExt, 'rb' ) as fileToTest :
				    # installedContent = fileToTest.read()
				  # if referenceContent != installedContent :
				    # print ("File %s corrupted." % fileInLocalExt)
				    # differentFile += 1
				  # else :
				    # print ("File %s has been verified." % fileInLocalExt)
				    # identicalFile += 1
				# else :
				  # self.__numNotFoundFiles += 1
				  # print ( 'Missing file %s' % fileInLocalExt )
			# else:
				# # element is a directory, tests it
				# directoryInLocalExt = join( self.__localExtPath, normalizeNameTruncated )
				# if not os.path.lexists(directoryInLocalExt):
				  # print ( 'Missing directory %s' % directoryInLocalExt )
				  # self.__numNotFoundDirectories += 1

		# # Closes package
		# zip.close()

		# # Prints statistics
		# self.__printStatistics()

		# if differentFile > 1:
			# print (	"%i different files," % differentFile ),
		# else:
			# print (	"%i different file," % differentFile ),

		# if identicalFile > 1:
			# print (	"%i identical files." % identicalFile )
		# else:
			# print (	"%i identical file." % identicalFile )





### class sbfPakCmd to implement interactive mode ###
import cmd

# Remove '-' as readline delimiter
try:
	import readline
	delims = readline.get_completer_delims()
	for elt in ['-', '*', '?', '[', ']']:
		delims = delims.replace(elt, '')
	readline.set_completer_delims( delims )
except ImportError as e:
	print ('sbfWarning: python module pyreadline is not installed.')


# @todo commands testArchive and testInstalled
class sbfPakCmd( cmd.Cmd ):

	def __init__( self, packagingSystem ):
		cmd.Cmd.__init__(self)
		self.__packagingSystem = packagingSystem

	# Commands
	def help_exit( self ):
		print "Usage: exit"
		print "Exit the interpreter."

	def do_exit( self, param ):
		return True

	def do_EOF( self, param ):
		print ('\n')
		return True

	def help_EOF( self ):
		self.help_exit()

	def help_listAvailable( self ):
		print ("Usage: listAvailable [packageNameFilter]\nPrint the list of available packages in repositories using a filter specified using the glob syntax.")

	def do_listAvailable( self, params ):
		parameterList = params.split()
		if len(parameterList) not in [0, 1]:
			self.help_list()
			return

		# Initializes pattern
		if len(parameterList) == 1 :
			if isAGlobPattern(parameterList[0]):
				pattern = parameterList[0]
			else:
				pattern = parameterList[0] + '*'
		else:
			pattern = '*'

		# Calls list method
		self.__packagingSystem.listAvailable( pattern, True )



	def help_listInstalled( self ):
		print ("Usage: listInstalled [packageNameFilter]\nPrint the list of the installed packages, filtered using packageNameFilter, in the current 'local/localExt' directories.")

	def do_listInstalled( self, params ):
		parameterList = params.split()
		if len(parameterList) not in [0, 1]:
			self.help_list()
			return

		# Initializes pattern
		if len(parameterList) == 1 :
			if isAGlobPattern(parameterList[0]):
				pattern = parameterList[0]
			else:
				pattern = parameterList[0] + '*'
		else:
			pattern = '*'

		# Calls list method
		self.__packagingSystem.listInstalled( pattern, True )


	def help_install( self ):
		print ("Usage: install packageNameFilter\nSearch in repositories all packages using the given packageNameFilter and install them in the current 'local/localExt' directories.")
		print ("Example: install glm* to install glm, glm-runtime, glm-runtime-debug and glm-runtime-release.")


	def __do_install__( self, filter, forced = False ):
		if isAGlobPattern(filter):
			packageFilenames = self.__packagingSystem.listAvailable( filter, False )
		else:
			packageFilename = self.__packagingSystem.getPackageFilename( filter )
			if packageFilename:
				packageFilenames = [packageFilename]
			else:
				packageFilenames = None

		if not packageFilenames:
			print ("No package selected by filter '{}'".format(filter))
			return

		for packageFilename in sorted(packageFilenames):
			# Call install method
			self.__packagingSystem.install( packageFilename, forced )


	def do_install( self, params ):
		parameterList = params.split()
		if len(parameterList) not in [1]:
			self.help_install()
			return

		self.__do_install__(parameterList[0])
		

	def complete_install( self, text, line, begidx, endidx ):
		if isAGlobPattern(text):
			return [text]
		else:
			return self.__packagingSystem.listAvailablePackageName( text + '*' )


	def help_installForced( self ):
		print ("Usage: installForced packageNameFilter\nSearch in repositories all packages using the given packageNameFilter and install them in the current 'local/localExt' directories.")
		print ("Example: installForced glm* to install glm, glm-runtime, glm-runtime-debug and glm-runtime-release.")


	def do_installForced( self, params ):
		parameterList = params.split()
		if len(parameterList) not in [1]:
			self.help_install()
			return

		self.__do_install__(parameterList[0], True)


	def complete_installForced( self, text, line, begidx, endidx ):
		return self.complete_install(text, line, begidx, endidx )


	def help_remove( self ):
		print ("Usage: remove packageNameFilter\nRemove from 'local/localExt' all files and directories installed by all packages selected by the given packageNameFilter.")
		print ("Example: remove glm* to remove glm, glm-runtime, glm-runtime-debug and glm-runtime-release.")

	def do_remove( self, params ):
		parameterList = params.split()
		if len(parameterList) not in [1]:
			self.help_remove()
			return

		filter = parameterList[0]

		if isAGlobPattern(filter):
			packageNames = self.__packagingSystem.listInstalled( filter, False )
		else:
			packageNames = [filter]

		if not packageNames:
			print ("No package selected by filter '{}'".format(filter))
			return

		for packageName in sorted(packageNames):
			# Call remove method
			self.__packagingSystem.remove( packageName )

	def complete_remove( self, text, line, begidx, endidx ):
		if isAGlobPattern(text):
			return [text]
		else:
			return self.__packagingSystem.listInstalled( text + '*')


	def help_mkpak( self ):
		print ("Usage: mkpak packageNameFilter\nRetrieves, builds and creates sbf package(s) for external dependencies selected by the given packageNameFilter (like boost, qt and so on).")

	def do_mkpak( self, params ):
		parameterList = params.split()
		if len(parameterList) != 1:
			self.help_mkpak()
			return

		filter = parameterList[0]

		if isAGlobPattern(filter):
			packageNames = self.__packagingSystem.mkdbListPackage(filter)
		else:
			if filter in self.__packagingSystem.mkdbListPackage('*'):
				packageNames = [filter]
			else:
				packageNames = []

		for packageName in sorted(packageNames):
			self.__packagingSystem.mkPak( packageName )
		if not packageNames:
			print ("No package selected by filter '{}'".format(filter))

	def complete_mkpak( self, text, line, begidx, endidx ):
		if isAGlobPattern(text):
			return [text]
		else:
			return sorted(self.__packagingSystem.mkdbListPackage( text + '*' ))


def runSbfPakCmd( sbf ):
	shell = sbfPakCmd( PackagingSystem(sbf) )
	shell.cmdloop("Using compiler {CCVERSION} with {ARCHITEXTURE} architecture on a {PLATFORM} system.\n\nWelcome to interactive mode of sbfPak".format(CCVERSION=sbf.myCCVersion, PLATFORM=sbf.myPlatform, ARCHITEXTURE=sbf.myArch))
