# SConsBuildFramework - Copyright (C) 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from sbfTools import locateProgram
from sbfUtils import subprocessGetOuputCall, nopAction, stringFormatter

try:
	from SCons.Script import *
except ImportError as e:
	print ('sbfWarning: unable to import SCons.Script')

from os.path import join


def sevenZipExtract( pathArchive, outputDir, verbose = True ):
	"""Extracts files from archive pathArchive with their full paths in the current directory, or in an output directory if specified."""
	path7z = locateProgram( '7z' )
	if not len(path7z):
		print ('sbfError: unable to find 7Zip extractor.')
		return False
	
	cmdLine = [ join(path7z, '7z'), 'x', pathArchive, '-y' ]
	if outputDir:
		cmdLine.append( '-o{0}'.format(outputDir) )
	
	return subprocessGetOuputCall( cmdLine, verbose )

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
