# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_qt3support( IUse ):
	cppModules = ['Qt3Support']
	linkModules = ['Qt3Support']
	# Adding libraries needed by Sofa version of Qt3Support
	linkModules += ['QtSQL', 'QtXml', 'QtNetwork', 'QtSvg', 'QtOpenGL'] # @todo remove with sbf version of qt
	linkVersionPostfix = '4'

	def getName( self ):
		return 'qt3support'

	def getVersions( self ):
		return ['4-8-5']

	def getCPPDEFINES( self, version ):
		cppDefines = [ 'QT_QT3SUPPORT_LIB', 'QT3_SUPPORT' ]
		return cppDefines

	def getCPPPATH( self, version ):
		return self.cppModules

	def getLIBS( self, version ):
		if self.platform == 'win':
			if self.config == 'release':
				libs = [ module + self.linkVersionPostfix for module in self.linkModules ]
			else:
				libs = [ module + 'd' + self.linkVersionPostfix for module in self.linkModules ]
			return libs, []

	def getPackageType( self ):
		return 'NoneAndNormal'
