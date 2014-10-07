# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_poppler( IUse ):
	"""poppler needs freetype2, zlib and libpng from gtkmm 2.22.0-2"""

	def getName( self ):
		return 'poppler'

	def getVersions( self ):
		return ['0-16-5']

	def getLIBS( self, version ):
		if self.config == 'release' :
			return ['poppler', 'poppler-cpp'], []
		else:
			return ['poppler-d', 'poppler-cpp-d'], []

	def hasRuntimePackage( self, version ):
		return True
