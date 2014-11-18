# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier, Philippe Sengchanpheng.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier
# Author Philippe Sengchanpheng

class Use_stbImageWrite( IUse ):
	def getName( self ):
		return "stbImageWrite"

	def getVersions( self ):
		return [ '0-95' ]

	def getCPPPATH( self, version ):
		return ['stb']

#	def getLicenses( self, version ):
#		return []

	def hasRuntimePackage( self, version ):
		return True