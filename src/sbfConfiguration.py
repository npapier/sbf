# SConsBuildFramework - Copyright (C) 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import sys
from os.path import join

from sbfEnvironment import Environment
from sbfPaths import Paths
from sbfTools import locateProgram, getPathsForRuntime, getPathsForTools
from sbfUses import getPathsForSofa

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
		print ('Target sbfConfigure* not yet implemented on {0} platform.'.format(sys.platform))


def _sbfUnconfigure( pathsToRemove, verbose ):
	if sys.platform == 'win32':
		environment = Environment()
		paths = Paths( environment.get('PATH', output=verbose) )
		paths.removeList( pathsToRemove )
		paths.removeAllNonExisting( verbose )
		if verbose:	print
		environment.set('PATH', paths.getString(), output=verbose)
	else:
		print ('Target sbfUnconfigure* not yet implemented on {0} platform.'.format(sys.platform))


def _getSBFRuntimePaths( sbf ):
	prependList = []
	appendList  = []

	# Prepends $SCONS_BUILD_FRAMEWORK in PATH for 'scons' file containing scons.bat $*
	prependList.append( sbf.mySCONS_BUILD_FRAMEWORK )

	# Adds C:\PythonXY (where C:\PythonXY is the path to your python's installation directory) to your PATH environment variable.
	# This is important to be able to run the Python executable from any directory in the command line.
	pythonLocation = locateProgram('python')
	appendList.append( pythonLocation )

	# Adds c:\PythonXY\Scripts (for scons.bat)
	appendList.append( join(pythonLocation, 'Scripts') )

	#
	return (prependList, appendList)


# Public interface
def sbfConfigure( sbf, takeCareOfSofa = True, verbose = True ):
	toPrepend = getPathsForRuntime(sbf)
	if takeCareOfSofa:
		toPrepend = getPathsForSofa(True) + toPrepend

	sbfRuntimePaths = _getSBFRuntimePaths( sbf )

	_sbfConfigure( toPrepend + sbfRuntimePaths[0], sbfRuntimePaths[1], verbose )


def sbfUnconfigure( sbf, takeCareOfSofa = True, takeCareOfSBFRuntimePaths = False, verbose = True ):
	toRemove = getPathsForRuntime(sbf)
	if takeCareOfSofa:
		toRemove = getPathsForSofa(True) + toRemove

	if takeCareOfSBFRuntimePaths:
		SBFRuntimePaths = _getSBFRuntimePaths(sbf) 
		toRemove += SBFRuntimePaths[0]
		toRemove += SBFRuntimePaths[1]

	_sbfUnconfigure( toRemove, verbose )


def sbfConfigureTools( sbf ):
	toAppend = getPathsForTools()
	_sbfConfigure( [], toAppend )


def sbfUnconfigureTools( sbf ):
	toRemove = getPathsForTools()
	_sbfUnconfigure( toRemove )
