# SConsBuildFramework - Copyright (C) 2005, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import glob
import os
import string
import sys

# To be able to use sbfUses.py without SCons
try:
	import SCons.Errors
except ImportError as e:
	pass

from sbfTools import *
from sbfVersion import splitUsesName

# Used by sbfVCProjTarget.py
def convertCPPPATHToAbs( env, cppPaths ):
	cppPathsAbs = []
	for cppPath in cppPaths:
		if os.path.isabs(cppPath):
			cppPathsAbs.append( cppPath )
		else:
			# Converts to absolute path
			cppPathsAbs.append( os.path.join( env.sbf.myIncludesInstallExtPaths[0], cppPath ) )
	return cppPathsAbs

###
class IUse :
	platform	= None
	config		= None

	# See SConsBuildFramework class
	cc					= None
	ccVersionNumber		= None
	isExpressEdition	= None
	ccVersion			= None

	@classmethod
	def initialize( self, platform, config, cc, ccVersionNumber, isExpressEdition, ccVersion ):
		self.platform	= platform
		self.config		= config

		#
		self.cc					= cc
		self.ccVersionNumber	= ccVersionNumber
		self.isExpressEdition	= isExpressEdition
		self.ccVersion			= ccVersion

	def getName( self ):
		raise StandardError("IUse::getName() not implemented")

	# Returns the list of version supported for this package.
	# The first element of the returned list is the default version (see use alias for more informations).
	def getVersions( self ):
		return []
		#raise StandardError("IUse::getVersions() not implemented")

	def getRequirements( self, version ):
		"""Returns a list of packages required (i.e. uses), by this package for the given version.
			@remark a package is specified using same schema as 'uses' option"""
		return []

	# for compiler
	def getCPPDEFINES( self, version ):
		return []

	def getCPPFLAGS( self, version ):
		return []

	def getCPPPATH( self, version ):
		return []

	# for linker
	def getLIBS( self, version ):
		return [], []

	def getLIBPATH( self, version ):
		return [], []


	# for packager
	# @todo bitfield hasPak, redistLibs, redistLicenses...
	def getPackageType( self ):
		"""	None			(no package, i.e. installed in the system (opengl), without files (gtkmmext), include in another package (glibmm in gtkmm))
			NoneAndNormal	(no package (like None), but getLIBS() and getLicenses() must be redistributed. Example: sofa)
			Normal			(indicate that this 'uses' is provided by an sbf package, that getLIBS() must be redistributed and that licenses files from package must be redistributed too.)."""
		return 'Normal'

	def getDbg( self, version ):
		"""@return a list of file containing debug informations (PDB on Windows platform)."""
		return []

	def getLicenses( self, version ):
		"""@return None to indicate that license file(s) could be found automatically (by using the naming rule of sbf package).
		Returns [] to explicitly specify that there is no license file at all (provided by another 'uses', like glibmm/gtkmm).
		Returns [...] to explicitly specify one or more license file(s)"""
		return []

	def hasDevPackage( self, version ):
		"""Returns True to inform that a developpement package have to be installed, false otherwise. Used by 'pakUpdate' target."""
		return self.getPackageType() == 'Normal'

	def hasRuntimePackage( self, version ):
		"""Returns True to inform that a deployment package have to be installed, false otherwise. Used by 'pakUpdate' target."""
		return False

	def hasPackage( self, useName, version ):
		"""Return True if useName has a package (runtime or development), otherwise returns False."""
		if '-runtime' in useName:
			return self.hasRuntimePackage( version )
		else:
			return self.hasDevPackage( version )

	# @todo deprecated ?
	def getRedist( self, version ):
		"""Returns the redistributable to include in nsis setup program. A redistributable must be a zip file or an executable available in SCONS_BUILD_FRAMEWORK/rc/nsis/ directory"""
		return []

	def __call__( self, useVersion, env, skipLinkStageConfiguration = False ):
		useNameVersion = self.getName() + " " + useVersion
#print ("Configures %s" % useNameVersion)

		### Configuration of compile stage
		# CPPDEFINES
		cppdefines = self.getCPPDEFINES( useVersion )
		if cppdefines != None :
			if len(cppdefines) > 0 :
				env.AppendUnique( CPPDEFINES = cppdefines )
		else:
			raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s (see CPPDEFINES)." % (useNameVersion, self.platform) )

		# CPPFLAGS
		cppflags = self.getCPPFLAGS( useVersion )
		if cppflags != None :
			if len(cppflags) > 0 :
				env.AppendUnique( CPPFLAGS = cppflags )
		else:
			raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s (see CPPFLAGS)." % (useNameVersion, self.platform) )

		# CPPPATH
		cpppath = self.getCPPPATH( useVersion )
		if cpppath != None :
			if len(cpppath) > 0:
				cppPathsAbs = convertCPPPATHToAbs( env, cpppath )
				if env.GetOption('weak_localext') and (self.getName() not in env['weakLocalExtExclude']):
					for path in cppPathsAbs :
						env.AppendUnique( CCFLAGS = ['${INCPREFIX}' + path ] )
				else:
					env.AppendUnique( CPPPATH = cppPathsAbs )
		else:
			raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s (see CPPPATH)." % (useNameVersion, self.platform) )

		### Configuration of link stage
		if skipLinkStageConfiguration:
			return

		# LIBS
		libs = self.getLIBS( useVersion )
		if (libs != None) and (len(libs) == 2) :
			if len(libs[0]) > 0:
				env.AppendUnique( LIBS = libs[0] )
		else:
			raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s (see LIBS)." % (useNameVersion, self.platform) )

		# LIBPATH
		libpath = self.getLIBPATH( useVersion )
		if (libpath != None) and (len(libpath) == 2) :
			if len(libpath[0]) > 0 :
				env.AppendUnique( LIBPATH = libpath[0] )
		else:
			raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s (see LIBPATH)." % (useNameVersion, self.platform) )


# Helpers
def generateAllUseNames( useName ):
	return [useName, useName + '-runtime', useName + '-runtime-release', useName + '-runtime-debug']

### Several IUse implementation ###
class UseRepository:
	__verbosity					= None
	__mySCONS_BUILD_FRAMEWORK	= None

	__repository	= {} # { useName : Use_useName() } with Use_useName = class Use_useName( IUse )
	__allowedValues = [] # ['opengl', 'boost1-56-0', 'boost1-55-0', ...]
	__alias			= {} # { boost : boost1-56-0 }

	__initialized	= False		# True after calling UseRepository.initialize()

	@classmethod
	def initialize( cls, sbf ):
		"""Called by sbfMain.py when SConsBuildFramework() has been initialized"""
		if cls.__initialized:
			raise SCons.Errors.InternalError("Try to initialize UseRepository twice.")

		# UseRepository initialization
		cls.__verbosity = sbf.myEnv.GetOption('verbosity')
		cls.__mySCONS_BUILD_FRAMEWORK = sbf.mySCONS_BUILD_FRAMEWORK

		# IUse initialization
		IUse.initialize(	sbf.myPlatform, sbf.myConfig,
							sbf.myCC, sbf.myCCVersionNumber, sbf.myIsExpressEdition, sbf.myCCVersion )

		# Populating repository with builtins 'uses'
		#cls.add( [	Use_swig(), Use_swigContrib(), Use_swigShp() ] )

		# Populating repository with 'uses' from src/uses/ directory
		# The following code is disabled, because initialization is done lazily when default.options specify a 'uses' option.
#		import time
#		start = time.clock()
#		for pathFilename in glob.glob( join(cls.__mySCONS_BUILD_FRAMEWORK, 'src/uses/*.py') ):
#			cls.addFromFilename( pathFilename )
#		end = time.clock()
#		print 'dynamic uses={} ms'.format( (end - start)*1000 )

		#
		cls.__initialized = True


	@classmethod
	def add( self, listOfIUseImplementation ):
		"""Adds each given instance of IUse in repository."""

		# Initializes repository
		if self.__verbosity:	print ("Adds in UseRepository :"),
		for use in listOfIUseImplementation :
			# Adds to repository
			name = use.getName().lower()

			self.__repository[ name ] = use
			if self.__verbosity:	print name,
			self.__allowedValues.append( name )

			# Configures allowed values and alias
			versions = use.getVersions()
			if len(versions) > 0:
				# This 'use' is for package with at least one explicit version number
				# Configures allowed values
				for version in versions:
					self.__allowedValues.append( name + version )

				# Configures alias
				self.__alias[name] = name + versions[0]

		self.__allowedValues = sorted(self.__allowedValues)
		if self.__verbosity:	print


	@classmethod
	def addFromFilename( cls, pathFilename ):
		"""Adds an implementation of IUse interface from file named pathFilename that have to contain Use_X() class with X the filename without extension"""

		filename = os.path.basename(pathFilename)
		g = { 'IUse' : IUse }
		try:
			execfile(pathFilename, g)						# @todo OPTME ?
			useName = 'Use_{}'.format(filename[:-3])
			UseRepository.add([g[useName]()])
		except IOError:
			if cls.__verbosity:	print ( 'No file {}'.format(pathFilename ) )
			return
		except KeyError:
			if cls.__verbosity:	print ( 'No {} in file {}'.format(useName, filename) )
			return
		except Exception as e:
			print e
			return


	@classmethod
	def addFromUseName( cls, useName ):
		pathFilename = join(cls.__mySCONS_BUILD_FRAMEWORK, 'src/uses/{}.py'.format(useName))
		cls.addFromFilename( pathFilename )

	@classmethod
	def getUse( self, name ):
		return self.__repository.get(name.lower(), None)

	@classmethod
	def gethUse( self, useNameVersion ):
		"""	@param useNameVersion	a single use passed to 'uses' option. In case of useNameVersion contains no version information, the first version of getVersions() is used.

			@return useName, useVersion, use

			@remark This function IS case sensitive for useNameVersion parameter
			"""

		useName, useVersion = splitUsesName( useNameVersion )
		lowerUseName = string.lower( useName )

		use = UseRepository.getUse( lowerUseName )
		if not use:
			# Try to load Use_useName() from src/uses/ directory
			self.addFromUseName( useName )
			use = UseRepository.getUse( lowerUseName )

		if use:
			if useVersion:
				# ex: useName=boost1-56-0
				return lowerUseName, useVersion, use
			else:
				# ex: useName=boost
				supportedVersions = use.getVersions()
				if supportedVersions:
					return lowerUseName, supportedVersions[0], use
				else:
					# @todo an error ? see all Use_() to choose the right behavior.
					return lowerUseName, '', use
		else:
			raise SCons.Errors.UserError("Unknown uses=['{}']".format(useNameVersion))


	@classmethod
	def getAllowedValues( self ):
		"""@todo deprecated"""
		return self.__allowedValues[:]

	@classmethod
	def getAlias( self ):
		"""@todo deprecated"""
		return self.__alias.copy()

def uses( self, lenv, uses, skipLinkStageConfiguration = False ):
	"""Updates environment 'lenv' using UseRepository"""
	if not isinstance(uses, list):	uses = [uses]

	for useNameVersion in uses:
		# Retrieves use, useName and useVersion
		useName, useVersion, use = UseRepository.gethUse( useNameVersion )
		# Configures environment with the 'use'
		use( useVersion, lenv, skipLinkStageConfiguration )
