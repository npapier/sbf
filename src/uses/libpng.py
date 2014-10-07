# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# @todo rename libpng => png
class Use_libpng( IUse ):
	def getName( self ):
		return 'libpng'

	def getVersions( self ):
		return [ '1-6-6' ]

	def getRequirements( self, version ):
		return ['zlib 1-2-8']

	def hasRuntimePackage( self, version ):
		return True