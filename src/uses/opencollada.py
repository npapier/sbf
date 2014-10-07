# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_opencollada( IUse ):
	def getName( self ):
		return "opencollada"

	def getVersions( self ):
		return ['865', '864', '768', '736']

	def getCPPPATH( self, version ):
		if self.platform == 'win':
			return [ 	'opencollada/COLLADAFramework/',
						'opencollada/COLLADABaseUtils/',
						'opencollada/COLLADABaseUtils/Math',
						'opencollada/COLLADASaxFrameworkLoader/',
						'opencollada/COLLADASaxFrameworkLoader/generated14',
						'opencollada/COLLADASaxFrameworkLoader/generated15',
						'opencollada/COLLADAStreamWriter/',
						'opencollada/GeneratedSaxParser/',
						'opencollada/MathMLSolver/',
						'opencollada/MathMLSolver/AST',
						'opencollada/LibXML/'
						'opencollada/LibXML/libxml',
						'opencollada/pcre/',
						'opencollada/libBuffer/',
						'opencollada/libBuffer/performanceTest',
						'opencollada/libftoa/',
						'opencollada/libftoa/performanceTest',
						'opencollada/libftoa/unitTest']
		else:
			return []		
		
	def getLIBS( self, version ):
		if self.platform == 'win':
			if self.config == 'release':
				libs = ['COLLADABaseUtils', 'COLLADAFramework', 'COLLADASaxFrameworkLoader', 'COLLADAStreamWriter', 'GeneratedSaxParser', 'pcre', 'MathMLSolver', 'LibXML', 'libBuffer', 'libftoa']
				return libs, []
			else:
				libs = ['COLLADABaseUtils-d', 'COLLADAFramework-d', 'COLLADASaxFrameworkLoader-d', 'COLLADAStreamWriter-d', 'GeneratedSaxParser-d', 'pcre-d', 'MathMLSolver-d', 'LibXML-d', 'libBuffer-d', 'libftoa-d']
				return libs, []
		else:
			libs = ['COLLADABaseUtils', 'COLLADAFramework', 'COLLADASaxFrameworkLoader', 'COLLADAStreamWriter', 'GeneratedSaxParser', 'pcre', 'MathMLSolver', 'LibXML', 'libBuffer', 'libftoa']
			return libs, []

