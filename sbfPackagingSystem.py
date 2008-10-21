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



# @todo statistics at the end of install/remove.
# @todo tests installation
# @todo verbose option
class PackagingSystem:
	#
	__localPath					= None
	__localExtPath				= None
	__repositoryPath			= None

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

		print



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


	def completeFilename( self, packageName ):
		return packageName + self.__my_Platform_myCCVersion + '.zip'



	def __init__( self ) :
		# Initializes the sbf main class to retrieve configuration
		from src.SConsBuildFramework import SConsBuildFramework
		sbf = SConsBuildFramework()
#print "myInstallPaths=", sbf.myInstallPaths[0]
#print "myInstallExtPaths=", sbf.myInstallExtPaths[0]
#print

		self.__localPath				= sbf.myInstallPaths[0]
		#os.path.normpath('d:\\_local')
		self.__localExtPath				= self.__localPath + 'Ext' + sbf.my_Platform_myCCVersion
		self.__repositoryPath 			= os.path.join( self.__localExtPath, 'pak' )						# @todo should be a sbf option

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

		# Tests existance of pak repository directory
		if os.path.isdir( self.__repositoryPath ) :
			print "Found package repository in %s" % self.__repositoryPath
		else :
			print "Package repository not found in %s" % self.__repositoryPath
			exit(1)
		print



	def info( self, filename, pattern ):

		# Adds repository path to filename
		pathFilename = os.path.join( self.__repositoryPath, filename )

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



	def install( self, filename ):

		# Adds repository path to filename
		pathFilename = os.path.join( self.__repositoryPath, filename )

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
			#else element is a directory, nothing to do

		# Closes package
		zip.close()

		# Prints statistics
		self.__printStatistics()



	def list( self, pattern = '' ):
		print ("Available package(s) in %s :" % self.__repositoryPath)
		for element in glob.glob( os.path.join(self.__repositoryPath, "*%s*.zip" % pattern) ):
			print os.path.basename(element)


# @todo try except => tests when a file is open
	def remove( self, filename ):

		# Adds repository path to filename
		pathFilename = os.path.join( self.__repositoryPath, filename )

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



	def testZip( self, filename ):
		# Tests zip
		pathFilename = os.path.join( self.__repositoryPath, filename )

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

# @todo usable as a library or a cmd
# @todo without SConstruct() stuff

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
	packagingSystem.list( pattern)
	exit(0)

#
pakName			= arguments[1]
completePakName = ''

splittedPakName	= os.path.splitext( pakName )
if len(splittedPakName[1]) == 0:
	completePakName = packagingSystem.completeFilename(pakName)
	print ("Full package name : %s" % completePakName)
else:
	completePakName = pakName

print

# @todo search
# @todo test
# @todo verbose mode (see sbf ?)

#
packagingSystem.testZip( completePakName )

if arguments[0] == 'info' :
	pattern = ''
	if len(arguments) == 3 :
		pattern = arguments[2]
	packagingSystem.info( completePakName, pattern )

if arguments[0] == 'install' :
	packagingSystem.install( completePakName )

if arguments[0] == 'remove' :
	packagingSystem.remove( completePakName )

if arguments[0] == 'test' :
	packagingSystem.test( completePakName )

exit(0)
