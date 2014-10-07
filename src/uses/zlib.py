# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_zlib( IUse ):
	def getName( self ):
		return 'zlib'

	def getVersions( self ):
		return [ '1-2-8' ]

	def getCPPDEFINES( self, version ):
		return ['ZLIB_WINAPI']

	def hasRuntimePackage( self, version ):
		return True
