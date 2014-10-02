# SConsBuildFramework - Copyright (C) 2012, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from sbfTools import locateProgram
from sbfUtils import subprocessGetOuputCall, subprocessCall2, nopAction, stringFormatter

import __builtin__
try:
	from SCons.Script import *
except ImportError as e:
	if not hasattr(__builtin__, 'SConsBuildFrameworkQuietImport'):
		print ('CCCsbfWarning: unable to import SCons.Script')

import glob
import sys
from os.path import join

# @todo cache locateProgram
def sevenZipExtract( pathArchive, outputDir, verbose = True, extractRootTarFiles = True ):
	"""Extracts files from archive pathArchive with their full paths in the current directory, or in an output directory if specified."""
	path7z = locateProgram( '7z' )
	if not len(path7z):
		print ('sbfError: unable to find 7Zip extractor.')
		return False

	cmdLine = [ join(path7z, '7z'), 'x', pathArchive, '-y' ]
	if outputDir:
		cmdLine.append( '-o{0}'.format(outputDir) )

	retVal = subprocessCall2( cmdLine )

	# Extract all .tar files found in the root of the output directory
	if extractRootTarFiles:
		for tarFile in glob.glob( join(outputDir, '*.tar') ):
			tarFile = join(outputDir, tarFile)
			# Depending on the platform, we will call tar or 7z once again.
			if sys.platform != 'win32': # @todo Use a more portable platform detection way.
				subRetVal = subprocessCall2( ['/bin/tar', '-C', outputDir, '-xvf', tarFile] )
			else:
				subRetVal = sevenZipExtract( tarFile, outputDir, verbose, False )
			
			#print 'subRetVal', subRetVal, '\n'	# @todo retVal
			os.remove( tarFile )
	return True

# @todo sevenZipCompress()



def __initializeEnv7z( lenv ):
	"""Initializes construction variable SEVENZIPCOM with path to 7z executable."""
	path7z = locateProgram( '7z' )
	if len(path7z)>0:
		#lenv['SEVENZIP_LOCATION'] = path7z
		lenv['SEVENZIPCOM'] = '\"{0}\"'.format( join(path7z, '7z' ) )
		#lenv['SEVENZIPCOMSTR']	= "Zipping ${TARGET.file}"
		lenv['SEVENZIPADDFLAGS']= "a -r"
		lenv['SEVENZIPFLAGS']	= "-bd"
		lenv['SEVENZIPSUFFIX']	= ".7z"
		#lenv['BUILDERS']['SevenZipAdd'] = Builder( action = Action( "$SEVENZIPCOM $SEVENZIPADDFLAGS $SEVENZIPFLAGS $TARGET $SOURCE" ) )#, lenv['SEVENZIPCOMSTR'] ) )
	#else nothing to do

def __printZip( target, source, localenv ) :
	return '\n' + stringFormatter( localenv, "Create zip archives" )

def create7ZipCompressAction( lenv, target, source, alias = None ):
	if 'SEVENZIPCOM' not in lenv:
		__initializeEnv7z(lenv)

	# cmd
	cmdLine = '{sevenZip} {addFlags} {flags} {target} {source}'.format( sevenZip=lenv['SEVENZIPCOM'], addFlags=lenv['SEVENZIPADDFLAGS'], flags=lenv['SEVENZIPFLAGS'], target=target, source=source)

	sevenZipAction = lenv.Command( target, 'dummy.in', cmdLine )
	if alias:
		lenv.Alias( alias, lenv.Command('zip_print.out', 'dummy.in', Action(nopAction, __printZip) ) )
		lenv.Alias( alias, sevenZipAction )
	return sevenZipAction
