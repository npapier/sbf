# SConsBuildFramework - Copyright (C) 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from sbfTools import locateProgram
from sbfUtils import subprocessCall

from os.path import join

def sevenZipExtract( pathArchive, outputDir, verbose = True ):
	"""Extracts files from archive pathArchive with their full paths in the current directory, or in an output directory if specified."""
	path7z = locateProgram( '7z' )
	if outputDir:
		cmdLine = '"{sevenZip}" x "{pathArchive}" -o"{outputDir}"'.format( sevenZip=join(path7z, '7z'), pathArchive = pathArchive, outputDir = outputDir )
	else:
		cmdLine = '"{sevenZip}" x "{pathArchive}"'.format( sevenZip=join(path7z, '7z'), pathArchive = pathArchive )

	return subprocessCall( cmdLine, verbose )
