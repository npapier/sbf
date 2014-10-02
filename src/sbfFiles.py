# SConsBuildFramework - Copyright (C) 2005, 2007, 2008, 2009, 2011, 2012, 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import fnmatch
import glob
import os
import re
import shutil

from os.path import basename, dirname, exists, isfile, isdir, join, split, splitext

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


def computeDepth( path ):
	"""Returns the depth of the path. Returns 0 for '.' and for '\\' on win and for '/' on posix. Returns 1 for '/first', 2 for '/a/b' and so on."""
	path = os.path.normpath( path )
	if path == '.':
		return 0

	countNonEmpty = 0
	for elt in path.split( os.sep ):
		if len(elt) > 0:
			countNonEmpty += 1
	return countNonEmpty


#########################################
###### Directory related functions ######
#########################################
def createDirectory( directory, verbose = True ):
	"""	Creates the directory if not already existing.
		@remark Creates all intermediate-level directories recursively if needed."""
	if not exists( directory ):
		if verbose:
			print ( 'Creates directory {0}'.format(directory) )
		os.makedirs( directory )

def removeDirectoryTree( directory, verbose = True ):
	"""Deletes an entire directory tree (if the directory is existing)"""
	if exists( directory ):
		if verbose:
			print ( 'Removes directory tree {0}'.format(directory) )
		shutil.rmtree( directory, True )
		#os.rmdir(pakDirectory)


##########################################
###### Copy/remove related function ######
##########################################

class GlobRegEx:
	def __splitPathname__( self, pathname ):
		match = re.match('^(?P<path>(?:[\w .-]+/)*)(?P<pattern>.*)$', pathname)
		if match:
			return match.group('path'), match.group('pattern'),
		else:
			raise AssertionError("Unable to split pathname '{0}'".format(pathname))

	def __init__( self, pathname = '.*', patternFlags = 0, pruneDirs = None, pruneFiles = None, ignoreDirs = False, ignoreFiles = False, recursive = False ):
		"""	@param pathname			path specification containing regular expression (see see re.compile()) to select matching files/directories
			@param patternFlags		see re.compile()
			@param pruneDirs		regular expression used to prune directories
			@param pruneFiles		regular expression used to prune files
			@param ignoreDirs		True to ignore all directories, False to look at directories
			@param ignoreFiles		True to ignore all files, False to look at files
			@param recursive		True to traverse the filesystem tree (top-down), False to stay at the top level of the tree
		"""

		(self.path, self.pattern) = self.__splitPathname__( pathname )
		self.patternFlags		= patternFlags
		self.reAccept			= re.compile( self.pattern, self.patternFlags )

		if pruneDirs:
			self.rePruneDirs	= re.compile( pruneDirs )
		else:
			self.rePruneDirs	= None

		if pruneFiles:
			self.rePruneFiles	= re.compile( pruneFiles )
		else:
			self.rePruneFiles	= None

		self.ignoreDirs			= ignoreDirs
		self.ignoreFiles		= ignoreFiles

		self.recursive			= recursive


	def __apply__( self, subdir ):
		# Collect all files and directories in subdir
		files = []
		dirs = []
		rootPath = join(self.path, subdir)
		for entry in os.listdir( rootPath ):
			absEntry = join(rootPath, entry)
			if isfile(absEntry):
				files.append(entry)
			else:
				dirs.append(entry)

		# Filter using match pattern and not matching pattern
		def applyFilter( container, reAccept, reReject, path ):
			if reReject:
				return [ join(path, elt) for elt in container if reAccept.match(elt) and (not reReject.match(elt)) ]
			else:
				return [ join(path, elt) for elt in container if reAccept.match(elt) ]

		# Applying filtering and taking care of ignoreDirs and ignoreFiles
		if self.ignoreDirs:
			dirs = []
		else:
			dirs = applyFilter( dirs, self.reAccept, self.rePruneDirs, subdir )

		if self.ignoreFiles:
			files = []
		else:
			files = applyFilter( files, self.reAccept, self.rePruneFiles, subdir )
		return dirs, files


	def apply( self, path = None ):
		"""@param path		allow to override path given in the constructor"""

		# Results
		self.dirs	= []
		self.files	= []

		# Initial value
		if path:
			self.path = path

		dirsToProcess = ['']

		# Collect files/directories
		for dir in dirsToProcess:
			(dirs, files) = self.__apply__( dir )
			self.dirs.extend( dirs )
			self.files.extend( files )

			if self.recursive:
				dirsToProcess.extend( dirs )


	def list( self ):
		return self.dirs + self.files

	def listFiles( self ):
		return self.files

	def listDirs( self ):
		return self.dirs



def shutilCopyTree( src, dst, symlinks=False, ignore=None ):
	createDirectory(dst, False )

	for item in os.listdir(src):
		s = join(src, item)
		d = join(dst, item)
		if isdir(s):
			shutilCopyTree(s, d, symlinks, ignore)
		else:
			#if not os.path.exists(d) or os.stat(src).st_mtime - os.stat(dst).st_mtime > 1:
			shutil.copy2(s, d)

def copy( source, destination, sourceDirectory = None, destinationDirectory = None, verbose = True ):
	"""Copies source to destination. Prepend sourceDirectory to source (resp. destinationDirectory to destination).
	If source is a file, then destination could be a file or a directory.
	If source is a directory, then destination must be a directory (existing or non existing).
		If source == destination, then sourceDirectory/dirname is copying in destinationDirectory/dirname with dirname = source = destination.
		If source != destination, then sourceDirectory/source is copying in destinationDirectory/destination.
	If source is a glob, then destination must be a directory (existing or not)
	If source is an enhanced version of glob created using GlobRegEx(), then destination must be a directory (existing or not)

	@remark If destination is a directory, it must be ended by a '/'
	@todo improves errors handling (exception instead of exit())."""

	# Prepares the copy
	if destinationDirectory:
		destination = join( destinationDirectory, destination )

	# Regular expression in source
	if isinstance(source, GlobRegEx):
		# source is a regular expression and destination must be a directory (existing or not)
		if destination[-1:] != '/':																		# @todo remove / ?
			# destination is not a directory
			print ('Destination {} is not a directory.'.format(destination))
			exit(1)

		# Creates destination if needed
		createDirectory(destination, verbose)

		# Collecting files to copy
		if sourceDirectory != None:
			source.apply( join(sourceDirectory, source.path) )
		else:
			source.apply()
		entries = source.list()
		if len(entries) == 0:
			print ("No files/directories matching '{}'".format(source.pattern) )
			exit(1)
		else:
			# Directories
			if source.recursive:
				for dir in source.listDirs():
					createDirectory( join(destination, dir), verbose )
			else:
				for dir in source.listDirs():
					if verbose:	print ( 'Copying tree {} in {}'.format(dir, destination) )
					shutil.copytree( join(source.path, dir), join(destination, dir) )

			# Files
			for file in source.listFiles():
				if verbose:	print ( 'Copying {} in {}'.format(file, join(destination, file)) )
				shutil.copyfile( join(source.path, file), join(destination, file) )
				shutil.copystat( join(source.path, file), join(destination, file) )
		return
	else:
		# Prepares the copy
		if sourceDirectory != None:
			source = join( sourceDirectory, source )

	# Copies a file
	if os.path.isfile(source):
		# Creates directory if needed
		if destination[-1:] == '/':
			# destination is a directory
			createDirectory(destination, verbose)
		else:
			# destination is not a directory
			newDir = dirname(destination)
			createDirectory(newDir, verbose)
		shutil.copy2( source, destination )
		if verbose:
			if os.path.isfile(destination):
				print ( 'Installing {}'.format(destination) )
			else:
				print ( 'Installing {}'.format( join(destination,basename(source)) ) )
	# Copies a directory
	elif os.path.isdir(source):
		if destination[-1:] != '/':
			# destination is not a directory
			print ('Destination {} is not a directory.'.format(destination))
			exit(1)
		if verbose:	print ( 'Populating {} using {}'.format(destination, source) )
		shutilCopyTree( source, destination )
	else:
		# source is a glob and destination must be a directory
		if destination[-1:] != '/':
			# destination is not a directory
			print ('Destination {} is not a directory.'.format(destination))
			exit(1)

		# Creates destination if needed
		createDirectory( destination, verbose )

		globMatch = glob.glob(source)
		if len(globMatch) == 0:
			if verbose:	print ('No files or directories for {}'.format(source) )
			exit(1)
		else:
			if verbose:	print ( 'Populating {} using {}'.format(destination, source) )
			for name in globMatch:
				if os.path.isdir(name):
					if verbose:	print ( 'Installing {} directory in {}'.format(name, destination) )
					shutil.copytree( name, join(destination, basename(name)) )
				else:
					if verbose:	print ( 'Installing {} in {}'.format(name, join(destination, basename(name))) )
					shutil.copyfile( name, join(destination, basename(name)) )
					shutil.copystat( name, join(destination, basename(name)) )


def copyTree( srcPathFilenames, dstPath, srcDir ):
	"""	@brief Copy the file(s) given by srcPathFilenames to the directory dstPath.

		@param srcPathFilenames		a list of path to files that would be copied
		@param dstPath				directory where files would be copied
		@param srcDir				files specified by srcPathFilenames are relative path to this directory"""
	for pathFilename in srcPathFilenames:
		(path, file) = split( pathFilename )
		dstDir = join( dstPath, path )

		if not exists( dstDir ):
			os.makedirs( dstDir )
		shutil.copy2( join(srcDir, pathFilename), join(dstDir, file) )


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
