#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2008, 2009, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from __future__ import with_statement

import fnmatch
import glob
import os
import zipfile



# @todo usable as a library or a cmd
# @todo without SConstruct() stuff

# @todo improves stats (see test() for missing stats), and install/remove/test() prints the same stats => flags to select interesting stats)).
# @todo renames into sbf-get and uses apt-get syntax.
# @todo search
# @todo verbose mode (see sbf ?)
# @todo verbose option
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



	def __init__( self, sbf ) :
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
				print ("WARNING: Package repository not found in %s" % path)
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


	# @todo filter on compiler
	# @todo the code of this method should be shared with list()
	def getListUsingPrefix( self, pattern = '' ):
		filenames = []
		for pakPath in self.__pakPaths:
#			print
#			print ("Available packages in %s :" % pakPath)
			elements = glob.glob( os.path.join(pakPath, "%s*.zip" % pattern) )
#			elements = glob.glob( os.path.join(pakPath, "*%s*.zip" % pattern) )
			sortedElements = sorted( elements )
			for element in sortedElements :
				filename = os.path.basename(element)

				filenameWithoutExt = os.path.splitext(filename)[0]
				splitted = filenameWithoutExt.split( self.__myPlatform, 1 )
				if len(splitted) == 1 :
					# The current platform not found in package filename, so don't print it
					continue
				name = splitted[0].rstrip('_')
#				print name.ljust(30), filename
				filenames.append(filename)
		return filenames


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
			print (	"%i identical files." % identicalFile )
		else:
			print (	"%i identical file." % identicalFile )



# class sbfPakCmd to implement interactive mode

import cmd

# @todo Improves help text
class sbfPakCmd( cmd.Cmd ):

	__packagingSystem = None

	def __init__( self, packagingSystem ):
		cmd.Cmd.__init__(self )
		self.__packagingSystem = packagingSystem

	def __locatePakName( self, pakName ):
		pathPakName = self.__packagingSystem.locatePackage( pakName )
		if pathPakName == None :
			print ("Unable to find package %s" % pakName )
		else:
			return pathPakName


	def completedefault( self, text, line, begidx, endidx ):
		filenames = self.__packagingSystem.getListUsingPrefix( text )
		return filenames

# Commands
	def help_exit( self ):
		print "Usage: exit"
		print "Exit the interpreter."

	def do_exit( self, param ):
		return True


	def help_list( self ):
		print "Usage: list [sub-package-name]"

	def do_list( self, params ):
		parameterList = params.split()
		if len(parameterList) not in [0, 1]:
			self.help_list()
			return

		# Initializes pattern
		pattern = ''
		if len(parameterList) == 1 :
			pattern = parameterList[0]

		# Calls list method
		self.__packagingSystem.list( pattern )

	def complete_list( self, text, line, begidx, endidx ):
		return []		# @todo Disables completion for list command. This method should work, but...


	def help_install( self ):
		print "Usage: install pakName"

	def do_install( self, params ):
		parameterList = params.split()
		if len(parameterList) not in [1]:
			self.help_install()
			return

		# Initializes pakName
		pathPakName = self.__locatePakName( parameterList[0] )
		if pathPakName != None :
			# Calls install method
			self.__packagingSystem.testZip( pathPakName )
			self.__packagingSystem.install( pathPakName )

	def help_remove( self ):
		print "Usage: remove pakName"

	def do_remove( self, params ):
		parameterList = params.split()
		if len(parameterList) not in [1]:
			self.help_remove()
			return

		# Initializes pakName
		pathPakName = self.__locatePakName( parameterList[0] )
		if pathPakName != None :
			# Calls remove method
			self.__packagingSystem.testZip( pathPakName )
			self.__packagingSystem.remove( pathPakName )

	def help_test( self ):
		print "Usage: test pakName"

	def do_test( self, params ):
		parameterList = params.split()
		if len(parameterList) not in [1]:
			self.help_test()
			return

		# Initializes pakName
		pathPakName = self.__locatePakName( parameterList[0] )
		if pathPakName != None :
			# Calls test method
			self.__packagingSystem.testZip( pathPakName )
			self.__packagingSystem.test( pathPakName )


	def help_info( self ):
		print "Usage: info pakName [sub-package-name]"

	def do_info( self, params ):
		parameterList = params.split()
		if len(parameterList) not in [1,2]:
			self.help_info()
			return

		# Initializes pakName
		pathPakName = self.__locatePakName( parameterList[0] )
		if pathPakName != None :
			# Retrieves pattern
			pattern = ''
			if len(parameterList) == 2 :
				pattern = parameterList[1]

			# Calls test method
			self.__packagingSystem.testZip( pathPakName )
			self.__packagingSystem.info( pathPakName, pattern )


def runSbfPakCmd( sbf ):
	shell = sbfPakCmd( PackagingSystem(sbf) )
	shell.cmdloop("Welcome to interactive mode of sbfPak")

#===============================================================================
# if __name__ == "SCons.Script" : # @todo Should be "__main__" ?
#	import sys
#	arguments = sys.argv[1:]
#	arguments.remove( '-f' )
#	arguments.remove( 'sbfPackagingSystem.py' )
#
#	shell = sbfPakCmd( PackagingSystem() )
#
#	if len(arguments) == 0 :
#		#
#		shell.cmdloop("Welcome to interactive mode of sbfPak")
#		exit(0)
#	else :
#		# Constructs a string containg the command to execute
#		command = ''
#		for arg in arguments :
#			command += arg + ' '
#
#		# Executes the command
#		shell.onecmd( command )
#		exit(0)
#===============================================================================
