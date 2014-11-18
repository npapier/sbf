# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier, Philippe Sengchanpheng.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier
# Author Philippe Sengchanpheng

class Use_stbImageResize( IUse ):
	def getName( self ):
		return "stbImageResize"

	def getVersions( self ):
		return [ '0-90' ]
		
	def getCPPPATH( self, version ):
		return ['stb']
		
#	def getLicenses( self, version ):
#		return []

	def hasRuntimePackage( self, version ):
		return True