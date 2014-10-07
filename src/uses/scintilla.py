# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_scintilla( IUse ):
	def getName( self ):
		return 'scintilla'

	def getVersions( self ):
		return [ '3-2-4', '3-2-3', '3-2-0']

	def getCPPDEFINES( self, version ):
		cppDefines = [ 'SCI_NAMESPACE' ]
		return cppDefines

	def getCPPPATH( self, version ):
		return ['Scintilla']

	def getLIBS( self, version ):
		if self.platform == 'win':
			if self.config == 'release':
				libs = ['ScintillaEdit3']
				return libs, libs
			else:
				libs = ['ScintillaEditd3']
				return libs, libs
		elif self.platform == 'posix':
			libs = ['ScintillaEdit']
			return libs,libs

	def hasRuntimePackage( self, version ):
		return version == '3-2-4'
