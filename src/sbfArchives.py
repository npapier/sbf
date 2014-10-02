# SConsBuildFramework - Copyright (C) 2010, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from os.path import join, splitext, normpath
import glob
import shutil
import tarfile
import zipfile


def __extractExtensionAndFormat__( filename ):
	"""@brief Returns extension of filename and format used by shutil.make_archive()"""
	extensionToFormat = {	'.zip'		: 'zip',
							'.tar.bz2'	: 'bztar',
							'.tar.gz'	: 'gztar',
							'.tgz'		: 'gztar' }
	for (extension, format) in extensionToFormat.iteritems():
		if filename.endswith(extension):
			return (extension, format)
	return ('', '')


def isArchiveFormatSupported( filename ):
	"""Returns True if the given filename is an archive supported by createArchive/extractArchive() functions, False otherwise."""
	print filename
	extension, format = __extractExtensionAndFormat__(filename)
	return len(extension)>0


def createArchive( archiveName, directory, verbose ):
	"""	@brief Create an archive file
		@param archiveName	name of the archive to create containing path and extension specifying format
		@param verbose		True to enable verbose mode, false otherwise
	"""
	extension, format = __extractExtensionAndFormat__(archiveName)
	if len(extension)==0:
		if verbose:	print ("Unsupported archive format for '{}'.".format(archiveName))
		return False

	archiveBaseName = archiveName[0:-len(extension)]
	#
	try:
		shutil.make_archive( archiveBaseName , format, root_dir=directory, verbose=verbose )
	except Exception as e:
			print e
			return False
	return True


def extractArchive( archiveFilename, extractionDirectory, verbose ):
	"""	@brief Extracts all members from the given archive to extractionDirectory path
		@param archiveFilename		name of the archive to extract
		@param extractionDirectory		directory where archive have to be extracted of None for the current working directory
		@param verbose				True to enable verbose mode, false otherwise
	"""

	def zipMembersGeneratorWithProgress(members, verbose):
		if verbose:
			for member in members:
				print ('Extracting {}'.format(member) )
				yield member	
		else:
			for member in members:
				yield member

	def tarMembersGeneratorWithProgress(members, verbose ):
		if verbose:
			for member in members:
				print ('Extracting {}'.format(member.name) )
				yield member			
		else:
			for member in members:
				yield member

	# zip
	if splitext(archiveFilename)[1] == '.zip':
		try:
			with zipfile.ZipFile( archiveFilename ) as arch:
				# Extracts
				arch.extractall( extractionDirectory, members= zipMembersGeneratorWithProgress(arch.namelist(), verbose))
		except Exception as e:
			print e
			return False
	# tar.bz2 and tar.gz and tgz
	elif archiveFilename.rfind('.tar.bz2') != -1 or archiveFilename.rfind('.tar.gz') != -1 or archiveFilename.rfind('.tgz') != -1:
		try:
			with tarfile.open( archiveFilename ) as tar:
				# Extracts
				tar.extractall( extractionDirectory, members = tarMembersGeneratorWithProgress(tar,verbose) )
		except Exception as e:
			print e
			return False
		return True
	else:
		assert( isArchiveFormatSupported(archiveFilename) )
		print ("Archive '{}' not yet supported".format(splitext(archiveFilename)[1]))
		return False
	return True


def getFilesAndDirectories( archiveFilename, oFiles, oDirectories ):
	"""	@brief Returns all files and directories found in the given archiveFilename
		@param archiveFilename		name of the archive to read
		@param oFiles				files found in archive
		@param oDirectories			directories found in archive

		@remark Supported format of archive are the same as tarfile python module.
	"""	
	with tarfile.open(archiveFilename) as tar:
		for member in tar:
			normalizedMember = normpath(member.name)
			if member.isfile():
				oFiles.append(normalizedMember)
			elif member.isdir():
				if normalizedMember!='.':	oDirectories.append(normalizedMember)
			else:
				assert( False )


# Helper
def extractAllTarFiles( directory, verbose ):
	"""	@brief Extract all .tar files found in the given directory. tar files are removed after extraction.
		@param directory	directory where archive files are looking for
	"""
	for tarFile in glob.glob( join(directory, '*.tar') ):
		tarFile = join(directory, tarFile)
		retVal = extractArchive(tarFile, directory, verbose)
		if retVal:
			os.remove( tarFile )
		else:
			return False
	return True