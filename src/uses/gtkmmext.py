# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_gtkmmext( IUse ):

	def getName( self ):
		return 'gtkmmext'

	def getVersions( self ):
		return [ '1-0' ]

	def getCPPFLAGS( self, version ):
		# compiler options
		if self.platform == 'win':
			if self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
				return ['/vd2']
		else:
			return []


	def getPackageType( self ):
		return 'None'
