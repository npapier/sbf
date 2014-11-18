# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier, Philippe Sengchanpheng.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier
# Author Philippe Sengchanpheng

class Use_stbImage( IUse ):
	def getName( self ):
		return "stbImage"

	def getVersions( self ):
		return [ '1-46' ]
	
	def getCPPPATH( self, version ):
		return ['stb']
		
#	def getLicenses( self, version ):
#		return []

	def hasRuntimePackage( self, version ):
		return True