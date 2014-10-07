# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_cairo( IUse ):

	def getName( self ):
		return 'cairo'

	def getVersions( self ):
		return ['1-10-0']


	def getCPPFLAGS( self, version ):
		if self.platform == 'win' :
			return [ '/wd4250' ]
		else:
			return []

	def getCPPPATH( self, version ):
		if self.platform == 'win' :
			return [ 'cairo', 'freetype2' ] # @todo add libpng14/fontconfig ?
		elif self.platform == 'posix' :
			return ['cairo']

	def getLIBS( self, version ):
		return ['cairo'], []

	def hasRuntimePackage( self, version ):
		return True
