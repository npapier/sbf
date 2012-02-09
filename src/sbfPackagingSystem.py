#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2008, 2009, 2010, 2011, 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import distutils.archive_util
import fnmatch
import glob
import os
import cPickle
import shutil
import subprocess
import types
import zipfile

from os.path import basename, dirname, exists, join, splitext
from sbfArchives import extractArchive
from sbfFiles import createDirectory, removeDirectoryTree, copy, removeFile, searchAllFilesAndDirectories, convertPathAbsToRel
from sbfSevenZip import sevenZipExtract
from sbfSubversion import splitSvnUrl, Subversion
from sbfUses import UseRepository
from sbfUtils import subprocessCall, removePathHead
from sbfVersion import splitPackageName, joinPackageName


# @todo PackagingSystem.verbose = False
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
	# Prints report on download advancement (each 128 kb)
	if ( size % 128 == 0):
		print ( '{0} kB \r'.format(size) ),
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



# @todo usable as a library or a cmd
# @todo without SConstruct() stuff

# @todo improves stats (see test() for missing stats), and install/remove/test() prints the same stats => flags to select interesting stats)).
# @todo renames into sbf-get and uses apt-get syntax.
# @todo search
# @todo verbose mode (see sbf ?)

# @todo creates a Statistics class
# @todo uses pylzma instead of zip
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
			print ( "%i override files." % self.__numOverrideFiles )
		else:
			print ( "%i override file." % self.__numOverrideFiles )


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

		if verbose:
			self.__verbose = verbose
		else:
			self.__verbose				= sbf.myEnv.GetOption('verbosity')

		self.__vcs						= sbf.myVcs

		self.__localPath				= sbf.myInstallPaths[0]
		self.__localExtPath				= self.__localPath + 'Ext' + sbf.my_Platform_myCCVersion
		self.__pakPaths 				= [ join( self.__mkPakGetDirectory() ) ]
		self.__pakPaths.extend( sbf.myEnv['pakPaths'] )

		self.__myConfig					= sbf.myConfig
		self.__myPlatform				= sbf.myPlatform
		self.__myCC						= sbf.myCC
		self.__myCCVersion				= sbf.myCCVersion
		self.__myCCVersionNumber		= sbf.myCCVersionNumber
		self.__myMSVSIDE				= sbf.myMSVSIDE

		self.__my_Platform_myCCVersion	= sbf.my_Platform_myCCVersion
		self.__libSuffix				= sbf.myEnv['LIBSUFFIX']
		self.__shLibSuffix				= sbf.myEnv['SHLIBSUFFIX']

		# Tests existance of localExt directory
		print
		if os.path.isdir( self.__localExtPath ) :
			print ("Found localExt in %s\n" % self.__localExtPath)
		else :
			print ("localExt not found in %s" % self.__localExtPath)
			createDirectory(self.__localExtPath)

		# Tests existance of pakPaths directory
		for path in self.__pakPaths :
			if os.path.isdir( path ) :
				print ("Found package repository in %s" % path)
			else :
				print ("WARNING: Package repository not found in %s" % path)
		print

		# Creates localExt directory
		createDirectory( self.getLocalExtSbfPakDBPath() )

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
		envDict	= {	'config'			: self.__myConfig,
					'platform'			: self.__myPlatform,
					'CC'				: self.__myCC,
					'CCVersion'			: self.__myCCVersion,
					'CCVersionNumber'	: self.__myCCVersionNumber,
					'MSVSIDE'			: self.__myMSVSIDE,

					'UseRepository'		: UseRepository,

					'buildDirectory'	: self.__mkPakGetBuildDirectory()
					}
		return envDict

	def mkdbListPackage( self, pattern = '' ):
		"""Returns the list of package description in mkdb.
		For example boost.py"""
		db = glob.glob( join( self.__mkdbGetDirectory(), '{0}*'.format(pattern) ) )
		return [ os.path.basename(elt) for elt in db ]



	def mkdbGetDescriptor( self, pakName ):
		"""Retrieves the dictionary named 'descriptor' from the mkdb database for the desired package"""
		globalsFileDict = {}
		localsFileDict = self.__getEnvironmentDict()
		execfile( join(self.__mkdbGetDirectory(), pakName), globalsFileDict, localsFileDict )

		return localsFileDict['descriptor']


	def mkPak( self, pakName ):
		"""Retrieves sources of a package, build them and creates the package"""
		pakDescriptor = self.mkdbGetDescriptor(pakName)

		if ('name' not in pakDescriptor) or ('version' not in pakDescriptor):
			print ("Package description without 'name' and/or 'version'")
			return

		# Creates the sandbox (i.e. private directory)
		createDirectory( self.__mkPakGetDirectory() )
		createDirectory( join(self.__mkPakGetDirectory(), 'cache' ) )
		createDirectory( join(self.__mkPakGetDirectory(), 'build' ) )

		# moves to sandbox
		backupCWD = os.getcwd()
		os.chdir( join(self.__mkPakGetDirectory() ) )

		# URLS (download and extract)
		extractionDirectory = self.__mkPakGetExtractionDirectory( pakDescriptor )
		removeDirectoryTree( extractionDirectory )

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

		import urllib
		import urlparse

		# URLS
		for url in pakDescriptor.get('urls', []):
			# Downloads
			filename = rsearchFilename( urlparse.urlparse(url).path )

			if not exists( join('cache', filename) ):
				print ( '* Retrieving %s from %s' % (filename, urlparse.urlparse(url).hostname ) )

				urllib.urlretrieve(url, filename= join('cache', filename), reporthook=reporthook_urlretrieve)
				print ( 'Done.' + ' '*16 )
			else:
				print ('* %s already downloaded.' % filename)
			print

			# Extracts
			print ( '* Extracting %s in %s...' % (filename, extractionDirectory) )
			try:
				extractArchive( join('cache', filename), extractionDirectory )
				print ( 'Done.\n' )
			except Exception, e:
				print ( 'Error encountered: %s\n' % (e) )
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
		if self.__myConfig == 'debug':
			configPostfix = '_D'
		else:
			configPostfix = ''

		pakDirectory = pakDescriptor['name'] + pakDescriptor['version'] + self.__my_Platform_myCCVersion + configPostfix + '/' # '/' is needed to specify directory to copy()
		sourceDir = join( extractionDirectory, pakDescriptor.get('rootDir','') )
		if not exists( sourceDir ):
			print ('{0} does not exist'.format( sourceDir) )
			exit(1)

		print ('* Creates package {0}'.format(pakDirectory[:-1]) )

		# Removes old directory
		removeDirectoryTree( pakDirectory )
		print

		# Creates directories
		createDirectory( pakDirectory )
		print

		# Copies license files
		for i, licenseFile in enumerate(pakDescriptor.get('license', [])):
			if len(pakDescriptor['license']) > 1:
				prefix = i
			else:
				prefix = ''
			copy(	licenseFile,
					join( 'license', '{0}license.{1}{2}.txt'.format( prefix, pakDescriptor['name'], pakDescriptor['version']) ),
					sourceDir, pakDirectory )
		print

		# Copies include files
		for include in pakDescriptor.get('include', []):
			if isinstance(include, tuple):
				copy( include[0], join( 'include', include[1] ), sourceDir, pakDirectory )
			else:
				copy( include, 'include/', sourceDir, pakDirectory )
		#else:
			print

		# Copies lib files
		for lib in pakDescriptor.get('lib', []):
			if isinstance(lib, tuple):
				copy( lib[0], join( 'lib', lib[1] ), sourceDir, pakDirectory )
			else:		
				copy( lib, 'lib/', sourceDir, pakDirectory )
		#else:
			print

		# Copies bin files
		for bin in pakDescriptor.get('bin', []):
			if isinstance(bin , tuple):
				copy( bin[0], join( 'bin', bin[1] ), sourceDir, pakDirectory )
			else:
				copy( bin, 'bin/', sourceDir, pakDirectory )
		#else:
			print

		# Copies custom files
		for elt in pakDescriptor.get('custom', []):
			if not isinstance(elt, tuple):
				elt = (elt,elt)
			copy( elt[0], elt[1], sourceDir, pakDirectory )
		#else:
			print

		# Creates zip
		pakDirectory = pakDirectory[:-1] # removes the last character '/'
		pakFile = pakDirectory + '.' + 'zip'
		print ( '* Creates archive of package {0}'.format(pakFile) )
		removeFile( pakFile )
		distutils.archive_util.make_zipfile( pakDirectory, pakDirectory, True )
		print ('Done.\n')

# @todo pprint

		# Restores old current working directory
		os.chdir( backupCWD )


	### PAK INFO ###
	def getLocalPackage( self, pakName, localDir ):
		"""Search package pakName in different repositories and copy in localDir (if needed).
		@return the path to the copy of pakName"""
		pathPakName = self.locatePackage( pakName )
		if not pathPakName:
			print ("Unable to find package {0}".format(pakName) )
			return

		localPakName = join( localDir, pakName )
		copyFile( pathPakName, localPakName, self.__verbose ) # @todo error proof
		return localPakName


	def printPackageNameAndVersion( self, packageName ):
		oPakInfo = {}
		oRelDirectories = []
		oRelFiles = []
		self.loadPackageInfo( packageName, oPakInfo, oRelDirectories, oRelFiles )
		print oPakInfo['name'].ljust(30), oPakInfo['version'].ljust(10)#, oPakInfo['platform'], oPakInfo['cc'], len(oRelFiles)

	def isInstalled( self, packageName ):
		sbfpakDir = self.getLocalExtSbfPakDBPath()
		return exists( join(sbfpakDir, packageName + '.info') )

	def isAvailable( self, pakName ):
		pathPakName = self.locatePackage(pakName)
		return pathPakName and (len(pathPakName)>0)

	def listInstalled( self, pattern = '', enablePrint = False ):
		"""Returns the list of installed packages."""

		files = glob.glob( join(self.getLocalExtSbfPakDBPath(), '*.info') )
		files = [splitext(basename(file))[0] for file in sorted(files)]

		retVal = []
		for file in files:
			if pattern:
				if file.find(pattern) == 0:
					if enablePrint: self.printPackageNameAndVersion(file)
					retVal.append( file )
				#else nothing to do
			else:
				if enablePrint: self.printPackageNameAndVersion(file)
				retVal.append(file)
		return retVal


	def savePackageInfo( self, pakInfo, relDirectories, relFiles ):
		"""@pre !isInstalled( pakInfo['name'] )"""

		sbfpakDir = self.getLocalExtSbfPakDBPath()
		pathInfoFile = join(sbfpakDir, pakInfo['name'] + '.info')

		with open( pathInfoFile, 'wb' ) as output:
			cPickle.dump( pakInfo, output )
			cPickle.dump( relDirectories, output )
			cPickle.dump( relFiles, output )

	def loadPackageInfo( self, pakName, oPakInfo, oRelDirectories = [], oRelFiles = [] ):
		"""@pre isInstalled( pakName )"""

		sbfpakDir = self.getLocalExtSbfPakDBPath()
		pathInfoFile = join(sbfpakDir, pakName + '.info')

		with open( pathInfoFile, 'rb' ) as input:
			oPakInfo.update( cPickle.load(input) )
			oRelDirectories.extend( cPickle.load(input) )
			oRelFiles.extend( cPickle.load(input) )



	###
	def listAvailable( self, pattern = '', enablePrint = True ):
		filenames = set()

		platformAndCCFilter = self.__my_Platform_myCCVersion
		if self.__myPlatform == 'win32':
			# Express and non express packages are similar, so don't filter on 'Exp'ress.
			platformAndCCFilter.replace('Exp', '', 1)

		for pakPath in self.__pakPaths:
			if enablePrint:
				print ("\nAvailable packages in %s :" % pakPath)
			elements = glob.glob( join(pakPath, "%s*.zip" % pattern) )
#			elements = glob.glob( join(pakPath, "*%s*.zip" % pattern) )
			sortedElements = sorted( elements )
			for element in sortedElements :
				filename = os.path.basename(element)
				filenameWithoutExt = splitext(filename)[0]

				splitted = filenameWithoutExt.split( platformAndCCFilter, 1 )
				if len(splitted) == 1:
				  # The current platform and compiler version not found in package filename, so don't print it
				  continue
				if enablePrint:
					print splitted[0].ljust(30), filename
				filenames.add(filename)
		return list(filenames)



	# @todo command-line option ?
	def locatePackage( self, pakName ):
		for path in self.__pakPaths :
			pathPakName = join( path, pakName )
			if os.path.isfile(pathPakName):
				return pathPakName


	# def testZip( self, pathFilename ):

		# # Tests file existance
		# if not os.path.lexists( pathFilename ):
			# print ("File %s does not exist." % pathFilename )
			# exit(1)

		# # Tests file type
		# if zipfile.is_zipfile( pathFilename ) == False :
			# print ("File %s is not a zip." % pathFilename)
			# exit(1)

		# # Opens and tests package
		# zip = zipfile.ZipFile( pathFilename )
		# print ('Tests %s\nPlease wait...' % os.path.basename(pathFilename) )
		# testzipRetVal = zip.testzip()
		# if testzipRetVal != None :
			# print ('bad file:%s' % testzipRetVal)
			# exit(1)
		# else :
			# print ('Done.\n')
		# zip.close()


	# def info( self, pathFilename, pattern ):

		# # Opens package
		# zip = zipfile.ZipFile( pathFilename )

		# # Prints info
		# sharedObjectList = []
		# staticObjectList = []
		# for name in zip.namelist() :
			# normalizeName = os.path.normpath( name )
			# if fnmatch.fnmatch( normalizeName, "*%s*" % pattern + self.__shLibSuffix ):
				# sharedObjectList.append( splitext(os.path.basename(normalizeName))[0] )
			# elif fnmatch.fnmatch( normalizeName, "*%s*" % pattern + self.__libSuffix ):
				# staticObjectList.append( splitext(os.path.basename(normalizeName))[0] )

		# #import pprint
		# print
		# print "static objects :"
		# pprintList( staticObjectList )

		# print
		# print "shared objects : "
		# pprintList( sharedObjectList )

		# # Closes package
		# zip.close()


	def install( self, pakName, forced = False ):
		pakInfo = splitPackageName( pakName )
		if not pakInfo:
			print ( 'The package named {0} is not available.'.format(pakName) )
			return

		if (not forced) and self.isInstalled( pakInfo['name'] ):
			print ( "Package {0} already installed.".format(pakInfo['name']) )
			return

		# Retrieves paths to several directories
		sbfpakDir = self.getLocalExtSbfPakDBPath()
		tmpDir = self.getLocalExtSbfPakDBTmpPath()
		removeDirectoryTree( tmpDir, self.__verbose )
		createDirectory( tmpDir )

		# Retrieves package pakName
		pathPakName = self.getLocalPackage( pakName, sbfpakDir )
		if not pathPakName:
			return

		print
		print ( "Installing package {0} using {1}...".format( pakName, pathPakName ) )
		print
		print ('Details :')

		# Extracts pak
		retVal = sevenZipExtract( pathPakName, tmpDir, self.__verbose )
		print

		# Collects all files and directories
		absFiles = []
		absDirectories = []
		searchAllFilesAndDirectories( tmpDir, absFiles, absDirectories, False )
		# Converts files and directories to be relative to tmp/localExt_platform_cc
		relFiles = [convertPathAbsToRel(tmpDir, file) for file in absFiles]
		relDirectories = [convertPathAbsToRel(tmpDir, dir) for dir in absDirectories]
		relFiles = removePathHead( relFiles )
		relDirectories = removePathHead( relDirectories )

		# Initializes statistics
		self.__initializeStatistics()

		# Creates directories
		print ('\nCreating directories...')
		for relDir in relDirectories:
			dir = join( self.__localExtPath, relDir )
			# Creates directory if needed
			if not exists( dir ):
				print ( 'Creating directory {0}'.format(dir) )
				os.makedirs( dir )
				self.__numNewDirectories += 1
			else:
				print ( 'Directory {0} already created'.format(dir) )

		# Copies files
		print ('\nInstalling files...')
		for absFile in absFiles:
			relFile = removePathHead( convertPathAbsToRel(tmpDir, absFile) )
			file = join( self.__localExtPath, relFile )
			if exists( file ):
				print ( 'Overriding {0}'.format( file ) )
				self.__numOverrideFiles += 1
			else:
				print ( 'Installing {0}'.format( file ) )
				self.__numNewFiles += 1
			shutil.copyfile( absFile, file )

		# Prints statistics
		self.__printStatistics()

		# Saves pak info
		self.savePackageInfo( pakInfo, relDirectories, relFiles )

		# Cleans
		removeDirectoryTree( tmpDir )


	def remove( self, packageName ):
		"""@pre isInstalled(packageName)"""

		if not self.isInstalled( packageName ):
			print ( "Package {0} is not installed.".format(packageName) )
			return

		# Load package info
		oPakInfo = {}
		oRelDirectories = []
		oRelFiles = []
		self.loadPackageInfo( packageName, oPakInfo, oRelDirectories, oRelFiles )
		pakName = joinPackageName( oPakInfo )

		# for debugging
		#print oPakInfo['name'].ljust(30), oPakInfo['version'].ljust(10)#, oPakInfo['platform'], oPakInfo['cc'], len(oRelFiles)
		#print pakName

		# Retrieves paths to several directories
		sbfpakDir = self.getLocalExtSbfPakDBPath()

		print ( "\nRemoving package {0} version {1}...\nDetails :".format( packageName, oPakInfo['version'] ) )

		# Initializes statistics
		self.__initializeStatistics()

		# Removes files
		print ('\nRemoving files...')
		for relFile in oRelFiles:
			absFile = join( self.__localExtPath, relFile )
			if exists(absFile):
				os.remove( absFile )
				self.__numDeletedFiles += 1
				print ( 'Removing {0}'.format(absFile) )
			else:
				self.__numNotFoundFiles += 1
				print ( '{0} already removed.'.format(absFile) )

		# Removes directories
		print ('\nRemoving directories...')
		for relDir in oRelDirectories:
			absDir = join( self.__localExtPath, relDir )
			if exists( absDir ):
				if len( os.listdir(absDir) ) == 0:
					os.rmdir( absDir )
					self.__numDeletedDirectories += 1
					print ( 'Removing {0}'.format(absDir) )
				else:
					self.__numNotEmptyDirectory += 1
					print ( 'Directory {0} not empty.'.format(absDir) )
			else:
				self.__numNotFoundDirectories += 1
				print ( '{0} already removed.'.format(absDir) )

		# Removes package archive and pak info
		os.remove( join(sbfpakDir, pakName) )
		os.remove( join(sbfpakDir, packageName + '.info') )

		# Prints statistics
		self.__printStatistics()


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

class sbfPakCmd( cmd.Cmd ):

	__packagingSystem = None

	def __init__( self, packagingSystem ):
		cmd.Cmd.__init__(self )
		self.__packagingSystem = packagingSystem

	def __mkdbLocatePackage( self, pakName ):
		packages = self.__packagingSystem.mkdbListPackage()
		if pakName not in packages:
			print ("Unable to find package {0}".format(pakName) )
		else:
			return pakName

# Commands
	def help_exit( self ):
		print "Usage: exit"
		print "Exit the interpreter."

	def do_exit( self, param ):
		return True

	def do_EOF( self, param ):
		print ('\n')
		return True


	def help_listAvailable( self ):
		print ("Usage: list [sub-package-name]\nList the available packages in repositories.")

	def do_listAvailable( self, params ):
		parameterList = params.split()
		if len(parameterList) not in [0, 1]:
			self.help_list()
			return

		# Initializes pattern
		pattern = ''
		if len(parameterList) == 1 :
			pattern = parameterList[0]

		# Calls list method
		self.__packagingSystem.listAvailable( pattern )


	def help_listInstalled( self ):
		print ("Usage: listInstalled [sub-package-name]\nList the installed packages in the current 'localExt' directory.")

	def do_listInstalled( self, params ):
		parameterList = params.split()
		if len(parameterList) not in [0, 1]:
			self.help_list()
			return

		# Initializes pattern
		if len(parameterList) == 1 :
			pattern = parameterList[0]
		else:
			pattern = ''

		# Calls list method
		self.__packagingSystem.listInstalled( pattern, True )


	def help_install( self ):
		print ("Usage: install pakName\nSearch in repositories the first package named 'pakName' and install it in the current 'localExt' directory.")

	def do_install( self, params ):
		parameterList = params.split()
		if len(parameterList) not in [1]:
			self.help_install()
			return

		pakName = parameterList[0]

		# Call install method
		self.__packagingSystem.install( pakName )

	def complete_install( self, text, line, begidx, endidx ):
		filenames = self.__packagingSystem.listAvailable( text, False )
		return filenames


	def help_installForced( self ):
		print ("Usage: installForced pakName\nSearch in repositories the first package named 'pakName' and install/reinstall it in the current 'localExt' directory.")

	def do_installForced( self, params ):
		parameterList = params.split()
		if len(parameterList) not in [1]:
			self.help_install()
			return

		pakName = parameterList[0]

		# Call install method
		self.__packagingSystem.install( pakName, True )

	def complete_installForced( self, text, line, begidx, endidx ):
		filenames = self.__packagingSystem.listAvailable( text, False )
		return filenames


	def help_remove( self ):
		print ("Usage: remove installedPackageName\nRemove from 'localExt' all files and directories installed by this package.")

	def do_remove( self, params ):
		parameterList = params.split()
		if len(parameterList) not in [1]:
			self.help_remove()
			return

		pakName = parameterList[0]
		# Calls remove method
		self.__packagingSystem.remove( pakName )

	def complete_remove( self, text, line, begidx, endidx ):
		packages = self.__packagingSystem.listInstalled( text )
		return packages

# @todo test
#	def help_test( self ):
#		print "Usage: test pakName"

#	def do_test( self, params ):
#		parameterList = params.split()
#		if len(parameterList) not in [1]:
#			self.help_test()
#			return

		# Initializes pakName
#		pathPakName = self.__locatePakName( parameterList[0] )
#		if pathPakName != None :
			# Calls test method
#			self.__packagingSystem.testZip( pathPakName )
#			self.__packagingSystem.test( pathPakName )


# @todo info printed in mkpak
#	def help_info( self ):
#		print "Usage: info pakName [sub-package-name]"

#	def do_info( self, params ):
#		parameterList = params.split()
#		if len(parameterList) not in [1,2]:
#			self.help_info()
#			return

#		# Initializes pakName
##		pathPakName = self.__locatePakName( parameterList[0] )
#		if pathPakName != None :
#			# Retrieves pattern
#			pattern = ''
#			if len(parameterList) == 2 :
#				pattern = parameterList[1]

			# Calls test method
#			self.__packagingSystem.testZip( pathPakName )
#			self.__packagingSystem.info( pathPakName, pattern )


	def help_mkpak( self ):
		print ("Usage: mkpak pakName\nRetrieves, build and create an sbf package for extern dependency (like boost, qt and so on).")

	def do_mkpak( self, params ):
		parameterList = params.split()
		if len(parameterList) != 1:
			self.help_mkpak()
			return

		# Initializes pakName
		pakName = self.__mkdbLocatePackage( parameterList[0] )
		if pakName:
			self.__packagingSystem.mkPak( pakName )

	def complete_mkpak( self, text, line, begidx, endidx ):
		packages = self.__packagingSystem.mkdbListPackage( text )
		return packages


def runSbfPakCmd( sbf ):
	shell = sbfPakCmd( PackagingSystem(sbf) )
	shell.cmdloop("Welcome to interactive mode of sbfPak\n")
