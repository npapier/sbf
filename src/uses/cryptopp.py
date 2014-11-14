# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_cryptopp( IUse ):
	def getName( self ):
		return 'Use_cryptopp'

	def getVersions( self ):
		return [ '5-6-2' ]

	def getCPPPATH( self, version ):
		return ['cryptopp']

	def getLIBS( self, version ):
		return ['cryptlib'], []

	def hasRuntimePackage( self, version ):
		return True
