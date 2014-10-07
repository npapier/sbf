# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_sigcpp( IUse ):

	def getName( self ):
		return 'sigcpp'

	def getVersions( self ):
		return [ '2-2-8' ]


	def getCPPPATH( self, version ):
		if self.platform == 'win' :
			return [ 'sigc++', '../lib/sigc++-2.0/include' ]
		elif self.platform == 'posix':
			sigcppPath = [ '/usr/include/sigc++-2.0','/usr/lib64/sigc++-2.0/include' ]

		return sigcppPath


	def getLIBS( self, version ):
		if self.platform == 'win':
			if version == '2-2-8':
				if self.config == 'release' :
					# RELEASE
					if self.cc == 'cl' and self.ccVersionNumber >= 11.0000 :
						libs = [ 'sigc-vc110-2_0' ]
					elif self.cc == 'cl' and self.ccVersionNumber >= 10.0000 :
						libs = [ 'sigc-vc100-2_0' ]
					elif self.cc == 'cl' and self.ccVersionNumber >= 9.0000 :
						libs = [ 'sigc-vc90-2_0' ]
					elif self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
						libs = [ 'sigc-vc80-2_0' ]
				else:
					# DEBUG
					if self.cc == 'cl' and self.ccVersionNumber >= 11.0000 :
						libs = [ 'sigc-vc110-d-2_0' ]
					elif self.cc == 'cl' and self.ccVersionNumber >= 10.0000 :
						libs = [ 'sigc-vc100-d-2_0' ]
					elif self.cc == 'cl' and self.ccVersionNumber >= 9.0000 :
						libs = [ 'sigc-vc90-d-2_0' ]
					elif self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
						libs = [ 'sigc-vc80-d-2_0' ]
			else:
				return

			return libs, []

		elif self.platform == 'posix':
			sigcpp = [ 'sigc-2.0' ]
			return sigcpp, []

	def hasRuntimePackage( self, version ):
		return True
