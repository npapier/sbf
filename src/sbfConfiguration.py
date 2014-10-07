# SConsBuildFramework - Copyright (C) 2012, 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import sys
from os.path import join

from sbfEnvironment import Environment
from sbfPaths import Paths
from sbfTools import locateProgram, getPathsForRuntime, getPathsForTools, prependToPATH, appendToPATH



###### Implementation of sbfConfigure and sbfUnconfigure targets #######
def _sbfConfigure( pathsToPrepend, pathsToAppend, verbose ):
	if sys.platform == 'win32':
		environment = Environment()
		paths = Paths( environment.get('PATH', output = verbose) )
		paths.prependList( pathsToPrepend, True )
		paths.appendList( pathsToAppend, True )
		print
		environment.set('PATH', paths.getString(), output = verbose)
	else:
		print ('Target sbfConfigure* not yet implemented on {} platform.'.format(sys.platform))


def _sbfUnconfigure( pathsToRemove, verbose ):
	if sys.platform == 'win32':
		environment = Environment()
		paths = Paths( environment.get('PATH', output=verbose) )
		paths.removeList( pathsToRemove )
# @todo asks user
		paths.removeAllNonExisting( verbose )
		if verbose:	print
		environment.set('PATH', paths.getString(), output=verbose)
	else:
		print ('Target sbfUnconfigure* not yet implemented on {0} platform.'.format(sys.platform))


# see bootstrap.py
def _getSBFRuntimePaths( sbf ):
	prependList = []
	appendList  = []

	# Prepends $SCONS_BUILD_FRAMEWORK in PATH for 'scons' file containing scons.bat $*
	prependList.append( sbf.mySCONS_BUILD_FRAMEWORK )

	# Adds C:\PythonXY (where C:\PythonXY is the path to your python's installation directory) to your PATH environment variable.
	# This is important to be able to run the Python executable from any directory in the command line.
	pythonLocation = locateProgram('python')
	prependList.append( pythonLocation )

	# Adds c:\PythonXY\Scripts (for scons.bat)
	appendList.append( join(pythonLocation, 'Scripts') )

	#
	return (prependList, appendList)


# Public interface
def getPATHForConfigure( sbf ):
	"""Returns (prependList, appendList)"""
	toPrepend = getPathsForRuntime(sbf)				# local/bin, localExt/bin and localExt/lib (@todo deprecated localExt/lib)
	sbfRuntimePaths = _getSBFRuntimePaths( sbf )	# ([$SCONS_BUILD_FRAMEWORK, C:\Python], [C:\Python\Scripts])
	return ( sbfRuntimePaths[0] + toPrepend, sbfRuntimePaths[1] )

def configurePATH( env, verbose = True ):
	"""@brief Configures the PATH environment variable used by the given environment env."""
	(prependList, appendList) = getPATHForConfigure(env.sbf)
	prependToPATH(env, prependList, verbose )
	appendToPATH(env, appendList, verbose )

def sbfConfigure( sbf, takeCareOfSofa = True, verbose = True ):	# @todo remove takeCareOfSofa
	(toPrepend, toAppend) = getPATHForConfigure(sbf)
	_sbfConfigure( toPrepend, toAppend, verbose )


def sbfUnconfigure( sbf, takeCareOfSofa = True, takeCareOfSBFRuntimePaths = False, verbose = True ): # @todo remove takeCareOfSofa
	deprecated = [join( sbf.myInstallDirectory, 'lib' )]
	toRemove = getPathsForRuntime(sbf) + deprecated

	if takeCareOfSBFRuntimePaths:
		SBFRuntimePaths = _getSBFRuntimePaths(sbf) 
		toRemove += SBFRuntimePaths[0]
		toRemove += SBFRuntimePaths[1]

	_sbfUnconfigure( toRemove, verbose )


def sbfConfigureTools( sbf, verbose = True ):
	toAppend = getPathsForTools(verbose)
	_sbfConfigure( [], toAppend, verbose )


def sbfUnconfigureTools( sbf, verbose = True ):
	toRemove = getPathsForTools(verbose)
	_sbfUnconfigure( toRemove, verbose )
