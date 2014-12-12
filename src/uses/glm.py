# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_glm( IUse ):
	def getName(self ):
		return 'glm'

	def getVersions( self ):
		return [ '0-9-5-4' ,'0-9-4-1', '0-9-3-4', '0-9-3-3', '0-8-4-1' ]

	def getCPPDEFINES( self, version ):
		return ['GLM_FORCE_RADIANS']
		# GLM_PRECISION_HIGHP_FLOAT ?

	def hasRuntimePackage( self, version ):
		return self.platform == 'posix' or self.cc == 'emcc'
