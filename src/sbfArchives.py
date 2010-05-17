# SConsBuildFramework - Copyright (C) 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from os.path import splitext
import tarfile
import zipfile



def isExtractionSupported( filename ):
	"""Returns True if the given filename is an archive supported by extractArchive() function, False otherwise."""
	extension = splitext(filename)[1]
	return extension in ['.zip', '.tar.bz2' 'tar.gz']


def extractArchive( filename, extractionDirectory = None ):
	"""Extracts all members from the archive to the current working directory or in extractionDirectory path."""
	if splitext(filename)[1] == '.zip':
		# Opens package
		zipFile = zipfile.ZipFile( filename )
		# Extracts
		zipFile.extractall( extractionDirectory )
		# Closes package
		zipFile.close()
	elif filename.rfind('.tar.bz2') != -1 or filename.rfind('.tar.gz') != -1:
		# Opens package	
		tar = tarfile.open( filename )
		# Extracts		
		tar.extractall( extractionDirectory )
		# Closes package		
		tar.close()
	else:
		# @todo Support 7z
		print ('Archive not yet supported')
		exit(1)
