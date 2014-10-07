# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_swigShp( IUse ):
	def getName( self ):
		return 'swigShp'

	def getVersions( self ):
		return ['3-0-2', '2-0-12']

	def hasRuntimePackage( self, version ):
		return True
