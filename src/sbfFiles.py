# SConsBuildFramework - Copyright (C) 2005, 2007, 2008, 2009, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import fnmatch
import glob
import os
import re
import shutil

from os.path import basename, dirname, join, splitext

####################################
###### Path related functions ######
####################################
def getNormalizedPathname( pathname ):
	"""Expands '~' and environment variables in the given pathname and normalizes it"""
	return os.path.normpath( os.path.expandvars(os.path.expanduser(pathname)) )


def convertPathAbsToRel( basePathName, absPathName ):
	"""Converts absolute pathname absPathName into a path relative to basePathName"""
	length = len(basePathName)
	return absPathName[length+1:]


#########################################
###### Directory related functions ######
#########################################
def createDirectory( directory, verbose = True ):
	"""Creates the directory if not already existing"""
	if not os.path.exists( directory ):
		if verbose:
			print ( 'Creates directory {0}'.format(directory) )
		os.mkdir( directory )

def removeDirectoryTree( directory, verbose = True ):
	"""Deletes an entire directory tree (if the directory is existing)"""
	if os.path.exists( directory ):
		if verbose:
			print ( 'Removes directory tree {0}'.format(directory) )
		shutil.rmtree( directory ) #, ignore_errors, onerror)
		#os.rmdir(pakDirectory)


###################################
###### Copy/remove related function ######
###################################

def copy( source, destination, sourceDirectory = None, destinationDirectory = None ):
	"""Copies source to destination.
	Prepend sourceDirectory to source (resp destinationDirectory to destination.
	If source is a file, then destination could be a file or a directory
	If source is a directory, then destination must be a directory
	If source is a glob, then destination must be a directory
	If destination is a directory, it must be ended by a '/'
	@todo improves errors handling (exception instead of exit()).
	@todo verbose = True parameter"""

	# Prepares the copy
	if sourceDirectory != None:
		source = join( sourceDirectory, source )
	if destinationDirectory != None:
		destination = join( destinationDirectory, destination )

	#if not os.path.exists(source):
	#	print ('{0} does not exist'.format(source))
	#	exit(1)

	# Copies a file
	if os.path.isfile(source):
		# Creates directory if needed
		if destination[-1:] == '/':
			# destination is a directory
			if not os.path.isdir(destination):
				print( 'Creates {0}'.format(destination) )
				os.makedirs( destination )
		else:
			# destination is not a directory
			newDir = dirname(destination)
			if not os.path.isdir(newDir):
				print( 'Creates {0}'.format(newDir) )
				os.makedirs( newDir )
		print ( 'Install {0}'.format(destination) )
		shutil.copy( source, destination )
	# Copies a directory
	elif os.path.isdir(source):
		if destination[-1:] != '/':
			# destination is not a directory
			print ('Destination {0} is not a directory.'.format(destination))
			exit(1)
		print ( 'Populates {0} using {1}'.format(destination, source) )
		shutil.copytree( source, destination )
	else:
		# source is a glob and destination must be a directory
		if destination[-1:] != '/':
			# destination is not a directory
			print ('Destination {0} is not a directory.'.format(destination))
			exit(1)

		# Creates destination if needed
		if not os.path.exists(destination):
			print( 'Creates {0}'.format(destination) )
			os.makedirs( destination )

		files = glob.glob(source)
		if len(files) == 0:
			print ('No files for {0}'.format(source) )
			exit(1)
		else:
			print ( 'Populates {0} using {1}'.format(destination, source) )
			for file in files:
				print ( 'Install {0} in {1}'.format(file, join(destination, basename(file))) )
				shutil.copyfile( file, join(destination, basename(file)) )


def removeFile( file, verbose = True ):
	"""Removes the file if and only if existing"""
	if os.path.exists( file ):
		if verbose:
			print ( 'Removes file {0}'.format(file) )
		os.remove( file )


#############################################
###### Searching files in a filesystem ######
#############################################

# Searches the filename in each directory given by searchPathList
# Returns the complete path with filename if found, otherwise None.
def searchFileInDirectories( filename, searchPathList ):
	for path in searchPathList :
		pathFilename = join( path, filename )
		if os.path.isfile( pathFilename ):
			return pathFilename

# Prune some directories
# Exclude/retain only a specific set of extensions for files
def searchFiles1( searchDirectory, pruneDirectories, allowedExtensions, oFiles ) :
	for dirpath, dirnames, filenames in os.walk( searchDirectory, topdown=True ):
		# prune directories
		prune = []
		for pruneDirectory in pruneDirectories :
			prune.extend( fnmatch.filter(dirnames, pruneDirectory) )
		for x in prune:
			###print 'prune', x
			dirnames.remove( x )

		for file in filenames:
			for extension in allowedExtensions :
				if ( splitext(file)[1] == extension ) :
					pathfilename = join(dirpath,file)
					oFiles += [pathfilename]
					break
#=======================================================================================================================
#			fileExtension = splitext(file)[1]
#			for extension in allowedExtensions :
#				if fileExtension == extension :
#					pathfilename = join(dirpath,file)
#					oFiles += [pathfilename]
#					break
#=======================================================================================================================
	###print 'oFiles=', oFiles


### searchdirectory				root path of the search
### oFiles						list where files are appended
### pruneDirectoriesPatterns
### allowedFilesRe				files matching this regular expression are append to oFiles
def searchFiles( searchDirectory, oFiles, pruneDirectoriesPatterns = [], allowedFilesRe = r".+" ) :
	compiledRe = re.compile( allowedFilesRe )
	for dirpath, dirnames, filenames in os.walk( searchDirectory, topdown = True ) :
		# FIXME: OPTME: replace fnmatch.filter() with dirnames = fnUNmatch.filter() or use module re
		# prune directories
		for pruneDirectoryPattern in pruneDirectoriesPatterns :
			dirnamesToRemove = fnmatch.filter(dirnames, pruneDirectoryPattern)
			for element in dirnamesToRemove :
				###print 'prune', element
				dirnames.remove( element )

		# get files
		for file in filenames :
			if compiledRe.match( file ) is not None :
				pathfilename = join(dirpath, file)
				oFiles.append(pathfilename)
	###print 'oFiles=', oFiles


# Gets all files
def searchAllFiles( searchDirectory, oFiles ) :
	for dirpath, dirnames, filenames in os.walk( searchDirectory, topdown=True ):
		for file in filenames:
			pathfilename = join(dirpath,file)
			oFiles.append(pathfilename)
	### print 'oFiles=', oFiles


# Gets all files and directories
def searchAllFilesAndDirectories( searchDirectory, oFiles, oDirectories, walkTopDown = True ):
	for dirpath, dirnames, filenames in os.walk( searchDirectory, topdown = walkTopDown ):
		for dir in dirnames:
			oDirectories.append( join(dirpath, dir) )
			#print 'oDirectories+=', join(dirpath, dir)
		for file in filenames:
			oFiles.append( join(dirpath, file) )
			#print 'oFiles+=', join(dirpath, file)
