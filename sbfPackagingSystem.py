#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2008, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from __future__ import with_statement

import fnmatch
import glob
import os
import zipfile



# @todo improves stats (see test() for missing stats), and install/remove/test() prints the same stats => flags to select interesting stats)).
# @todo renames into sbf-get and uses apt-get syntax.
# @todo search
# @todo verbose mode (see sbf ?)
# @todo cmd -- Support for line-oriented command interpreters
# @todo verbose option
# @todo usable as a library or a cmd
# @todo without SConstruct() stuff
class PackagingSystem:
	#
	__localPath					= None
	__localExtPath				= None
	__pakPaths					= []

	__myPlatform				= None
	__my_Platform_myCCVersion	= None
	__libSuffix					= None
	__shLibSuffix				= None


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



	def __computeDepth( self, path ) :
		return len( os.path.normpath( path ).split( os.sep ) )



	def __pprintList( self, list ) :
		listLength = len(list)
		currentString = '[ '

		for i, element in enumerate(list) :
			if len(currentString) + len(element) + 3 >= 120 :
				print currentString
				currentString = ''
			currentString += "'%s', " % element
		print currentString[0:-2] + " ]"



	def __init__( self ) :
		# Initializes the sbf main class to retrieve configuration
		from src.SConsBuildFramework import SConsBuildFramework
		sbf = SConsBuildFramework()

		self.__localPath				= sbf.myInstallPaths[0]
		self.__localExtPath				= self.__localPath + 'Ext' + sbf.my_Platform_myCCVersion
		self.__pakPaths 				= [os.path.join( self.__localExtPath, 'sbfPak' )]
		self.__pakPaths.extend( sbf.myEnv['pakPaths'] )

		self.__myPlatform				= sbf.myPlatform
		self.__my_Platform_myCCVersion	= sbf.my_Platform_myCCVersion
		self.__libSuffix				= sbf.myEnv['LIBSUFFIX']
		self.__shLibSuffix				= sbf.myEnv['SHLIBSUFFIX']

		# Tests existance of localExt directory
		print
		if os.path.isdir( self.__localExtPath ) :
			print ("Found localExt in %s" % self.__localExtPath)
		else :
			print ("localExt not found in %s" % self.__localExtPath)
			exit(1)

		# Tests existance of pakPaths directory
		for path in self.__pakPaths :
			if os.path.isdir( path ) :
				print ("Found package repository in %s" % path)
			else :
				print ("Package repository not found in %s" % path)
				exit(1)
		print



	# @todo filter on compiler
	def list( self, pattern = '' ):
		for pakPath in self.__pakPaths:
			print
			print ("Available packages in %s :" % pakPath)
			elements = glob.glob( os.path.join(pakPath, "*%s*.zip" % pattern) )
			sortedElements = sorted( elements )
			for element in sortedElements :
				filename = os.path.basename(element)

				filenameWithoutExt = os.path.splitext(filename)[0]
				splitted = filenameWithoutExt.split( self.__myPlatform, 1 )
				if len(splitted) == 1 :
					# The current platform not found in package filename, so don't print it
					continue
				name = splitted[0].rstrip('_')
				print name.ljust(30), filename


	def completeFilename( self, packageName ):
		return packageName + self.__my_Platform_myCCVersion + '.zip'


	# @todo command-line option ?
	def locatePackage( self, pakName ):
		for path in self.__pakPaths :
			pathPakName = os.path.join( path, pakName )
			if os.path.isfile(pathPakName):
				return pathPakName


	def testZip( self, pathFilename ):

		# Tests file existance
		if not os.path.lexists( pathFilename ):
			print ("File %s does not exist." % pathFilename )
			exit(1)

		# Tests file type
		if zipfile.is_zipfile( pathFilename ) == False :
			print ("File %s is not a zip." % pathFilename)
			exit(1)

		# Opens and tests package
		zip = zipfile.ZipFile( pathFilename )
		print ('Tests %s\nPlease wait...' % os.path.basename(pathFilename) )
		testzipRetVal = zip.testzip()
		if testzipRetVal != None :
			print ('bad file:%s' % testzipRetVal)
			exit(1)
		else :
			print ('Done.\n')
		zip.close()


	def info( self, pathFilename, pattern ):

		# Opens package
		zip = zipfile.ZipFile( pathFilename )

		# Prints info
		sharedObjectList = []
		staticObjectList = []
		for name in zip.namelist() :
			normalizeName = os.path.normpath( name )
			if fnmatch.fnmatch( normalizeName, "*%s*" % pattern + self.__shLibSuffix ):
				sharedObjectList.append( os.path.splitext(os.path.basename(normalizeName))[0] )
			elif fnmatch.fnmatch( normalizeName, "*%s*" % pattern + self.__libSuffix ):
				staticObjectList.append( os.path.splitext(os.path.basename(normalizeName))[0] )

		#import pprint
		print
		print "static objects :"
		self.__pprintList( staticObjectList )

		print
		print "shared objects : "
		self.__pprintList( sharedObjectList )

		# Closes package
		zip.close()



	def install( self, pathFilename ):

		# Opens package
		zip = zipfile.ZipFile( pathFilename )

		# Initializes statistics
		self.__initializeStatistics()

		#
		print
		print ( "Installs package using %s" % pathFilename )
		print
		print ('Details :')

		for name in zip.namelist() :
			normalizeName			= os.path.normpath( name )
			normalizeNameSplitted	= normalizeName.split( os.sep )

			normalizeNameTruncated	= None
			if len(normalizeNameSplitted) > 1 :
				normalizeNameTruncated = normalizeName.replace( normalizeNameSplitted[0] + os.sep, '' )
			else :
				continue

			if not name.endswith('/') :
				# element is a file
				fileInLocalExt = os.path.join( self.__localExtPath, normalizeNameTruncated )

				# Creates directory if needed
				if not os.path.lexists(os.path.dirname(fileInLocalExt)):
					print ( 'Creates directory %s' % fileInLocalExt )
					os.makedirs( os.path.dirname(fileInLocalExt) )
					self.__numNewDirectories += 1

				if os.path.isfile( fileInLocalExt ) :
					#print ( '%s already exists, so removes it.' % fileInLocalExt )
					os.remove( fileInLocalExt )
					self.__numOverrideFiles += 1
					print ( 'Override %s' % fileInLocalExt )
				else :
					self.__numNewFiles += 1
					print ( 'Installs %s' % fileInLocalExt )

				with open( fileInLocalExt, 'wb' ) as outputFile :
					outputFile.write( zip.read(name) )
					outputFile.flush()
			else:
				# element is a directory, try to create it
				directoryInLocalExt = os.path.join( self.__localExtPath, normalizeNameTruncated )
				if not os.path.lexists(directoryInLocalExt):
					print ( 'Creates directory %s' % directoryInLocalExt )
					os.makedirs( directoryInLocalExt )
					self.__numNewDirectories += 1

		# Closes package
		zip.close()

		# Prints statistics
		self.__printStatistics()


	# @todo try except => tests when a file is open
	def remove( self, pathFilename ):

		# Opens package
		zip = zipfile.ZipFile( pathFilename )

		# Initializes statistics
		self.__initializeStatistics()

		#
		print ( "Removes package installed using %s" % pathFilename )
		print
		print ('Details :')

		directories = []
		for name in zip.namelist() :
			normalizeName			= os.path.normpath( name )
			normalizeNameSplitted	= normalizeName.split( os.sep )

			normalizeNameTruncated	= None
			if len(normalizeNameSplitted) > 1 :
				normalizeNameTruncated = normalizeName.replace( normalizeNameSplitted[0] + os.sep, '' )
			else :
				continue

			if not name.endswith('/') :
				# element is a file
				fileInLocalExt = os.path.join( self.__localExtPath, normalizeNameTruncated )
				if os.path.isfile( fileInLocalExt ) :
					os.remove( fileInLocalExt )
					self.__numDeletedFiles += 1
					print ( 'Removes %s' % fileInLocalExt )
				else :
					self.__numNotFoundFiles += 1
					print ( '%s already removed.' % fileInLocalExt )
			else :
				# element is a directory
				directoryInLocalExt = os.path.join( self.__localExtPath, normalizeNameTruncated )
				directories.append( directoryInLocalExt )

		# Processes directories
		print

		sortedDirectories = sorted( directories, key = self.__computeDepth, reverse = True )

		for directory in sortedDirectories :
			if os.path.lexists(directory) :
				if len( os.listdir( directory ) ) == 0 :
					os.rmdir( directory )
					self.__numDeletedDirectories += 1
					print ( 'Removes %s' % directory )
				else :
					self.__numNotEmptyDirectory += 1
					print ( 'Directory %s not empty.' % directory )
			else :
				self.__numNotFoundDirectories += 1
				print ( '%s already removed.' % directory )

		# Closes package
		zip.close()

		# Prints statistics
		self.__printStatistics()



	def test( self, pathFilename ):

		# Opens package
		zip = zipfile.ZipFile( pathFilename )

		# Initializes statistics
		self.__initializeStatistics()
		differentFile	= 0
		identicalFile	= 0

		#
		print
		print ( "Tests package using %s" % pathFilename )
		print
		print ('Details :')

		for name in zip.namelist() :
			normalizeName			= os.path.normpath( name )
			normalizeNameSplitted	= normalizeName.split( os.sep )

			normalizeNameTruncated	= None
			if len(normalizeNameSplitted) > 1 :
				normalizeNameTruncated = normalizeName.replace( normalizeNameSplitted[0] + os.sep, '' )
			else :
				continue

			if not name.endswith('/') :
				# element is a file
				fileInLocalExt = os.path.join( self.__localExtPath, normalizeNameTruncated )

				# Tests directory
				if not os.path.lexists(os.path.dirname(fileInLocalExt)):
					print ( 'Missing directory %s' % os.path.dirname(fileInLocalExt) )
					self.__numNotFoundDirectories += 1

				if os.path.isfile( fileInLocalExt ):
					# Tests contents of the file
					referenceContent = zip.read(name)
					installedContent = ''
					with open( fileInLocalExt, 'rb' ) as fileToTest :
						installedContent = fileToTest.read()
					if referenceContent != installedContent :
						print ("File %s corrupted." % fileInLocalExt)
						differentFile += 1
					else :
						print ("File %s has been verified." % fileInLocalExt)
						identicalFile += 1
				else :
					self.__numNotFoundFiles += 1
					print ( 'Missing file %s' % fileInLocalExt )
			else:
				# element is a directory, tests it
				directoryInLocalExt = os.path.join( self.__localExtPath, normalizeNameTruncated )
				if not os.path.lexists(directoryInLocalExt):
					print ( 'Missing directory %s' % directoryInLocalExt )
					self.__numNotFoundDirectories += 1

		# Closes package
		zip.close()

		# Prints statistics
		self.__printStatistics()

		if differentFile > 1:
			print (	"%i different files," % differentFile ),
		else:
			print (	"%i different file," % differentFile ),

		if identicalFile > 1:
			print (	"%i identical files." % identicalFile ),
		else:
			print (	"%i identical file." % identicalFile ),

#
import sys
#print "argv=", sys.argv
arguments = sys.argv[1:]
arguments.remove( '-f' )
arguments.remove( 'sbfPackagingSystem.py' )

#print "arguments=", arguments

if not ( (len(arguments) in [1,2] and arguments[0] in ['list']) or \
(len(arguments) == 2 and arguments[0] in ['info', 'install', 'remove', 'test']) or \
(len(arguments) == 3 and arguments[0] in ['info']) ):
	print "Usage:"
	print " sbfPak install|remove|test pakName"
	print " sbfPak info pakName [sub-package-name]"
	print " sbfPak list [sub-package-name]"
	exit(1)

#
packagingSystem = PackagingSystem()

if arguments[0] == 'list' :
	# Initializes pattern
	pattern = ''
	if len(arguments) == 2 :
		pattern = arguments[1]
	# Calls list method
	packagingSystem.list( pattern )
	exit(0)

# Constructs the full package name (if needed)
pakName	= arguments[1]

if len(os.path.splitext( pakName )[1]) == 0:
	pakName = packagingSystem.completeFilename(pakName)

# Adds repository path to pakName
pathPakName = packagingSystem.locatePackage( pakName )
if pathPakName == None :
	print ("Unable to find package %s" % pakName )
	exit(1)

print ("Incoming package : %s" % pathPakName )
print

#
packagingSystem.testZip( pathPakName )

if arguments[0] == 'info' :
	pattern = ''
	if len(arguments) == 3 :
		pattern = arguments[2]
	packagingSystem.info( pathPakName, pattern )

if arguments[0] == 'install' :
	packagingSystem.install( pathPakName )

if arguments[0] == 'remove' :
	packagingSystem.remove( pathPakName )

if arguments[0] == 'test' :
	packagingSystem.test( pathPakName )

exit(0)
