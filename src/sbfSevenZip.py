# SConsBuildFramework - Copyright (C) 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from sbfUtils import subprocessCall



def sevenZipExtract( pathArchive, outputDir, verbose = True ):
	"""Extracts files from archive pathArchive with their full paths in the current directory, or in an output directory if specified."""
	if outputDir:
		cmdLine = '7z x "{pathArchive}" -o"{outputDir}"'.format( pathArchive = pathArchive, outputDir = outputDir )
	else:
		cmdLine = '7z x "{pathArchive}"'.format( pathArchive = pathArchive )

	return subprocessCall( cmdLine, verbose )
