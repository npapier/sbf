# SConsBuildFramework - Copyright (C) 2009, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from __future__ import with_statement

import os

from src.sbfFiles import getNormalizedPathname



def printSBFVersion() :
	print 'SConsBuildFramework version : %s' % getSBFVersion()


def getSBFVersion() :
	# Retrieves and normalizes SCONS_BUILD_FRAMEWORK
	sbfRoot = getNormalizedPathname( os.getenv('SCONS_BUILD_FRAMEWORK') )

	# Reads version number in VERSION file
	versionFile	= os.path.join(sbfRoot, 'VERSION')
	if os.path.lexists( versionFile ) :
		with open( versionFile ) as file :
			return file.readline()
	else :
		return "Missing %s file. So version number is unknown." % versionFile
