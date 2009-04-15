# SConsBuildFramework - Copyright (C) 2005, 2007, 2008, 2009, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

#from SCons.Script.SConsOptions import *
#from SCons.Script.SConscript import SConsEnvironment



import datetime
import glob
import os

from sbfFiles import *
from sbfRC import resourceFileGeneration
from sbfSubversion import *
from sbfUses import UseRepository, usesValidator, usesConverter, uses
from sbfUtils import *
from SCons.Environment import *
from SCons.Options import *
from SCons.Script import *



#from SCons.


#import SCons.Action
#import SCons.Util
#import SCons.Builder
#import SCons.Tool



def sbfPrintCmdLine( cmd, target, src, env ):
#	print ("beginning=%s" % cmd[:20])

	if cmd.startswith( 'sbf' ) :
		if cmd.startswith( 'sbfNull' ) :
			return
		else:
			return
	elif cmd.startswith( ('link /', 'link @', 'lib /', 'lib @' ) ) : # ('link /nologo', 'lib /nologo')
		print ('Linking %s' % str(os.path.basename(target[0].abspath)))
	elif cmd.startswith( 'mt /') : # 'mt /nologo'
		print ('Embedding manifest into %s' % str(os.path.basename(target[0].abspath)))
	else:
		print cmd

###### Functions for print action ######
def stringFormatter( lenv, message ) :
	columnWidth	= lenv['outputLineLength']
	retVal = (' ' + message + ' ').center( columnWidth, '-' )
	return retVal

def nopAction(target = None, source = None, env = None) :
	return 0

def printEmptyLine(target = None, source = None, env = None) :
	print ''

def printBuild( target, source, localenv ) :
	return stringFormatter( localenv, "Build %s" % localenv['sbf_projectPathName'] )

def printInstall( target, source, localenv ) :
	return stringFormatter(localenv, "Install %s files to %s" % (localenv['sbf_projectPathName'], localenv.sbf.myInstallDirectory) )

def printClean( target, source, localenv ) :
	return stringFormatter( localenv, "Clean %s files to %s" % (localenv['sbf_projectPathName'], localenv.sbf.myInstallDirectory) )

def printMrproper( target, source, localenv ) :
	return stringFormatter( localenv, "Mrproper %s files to %s" % (localenv['sbf_projectPathName'], localenv.sbf.myInstallDirectory) )

def printGenerate( target, source, localenv ) :
	return "Generating %s" % str(os.path.basename(target[0].abspath)) # @todo '\n' usage ?



###### SConsBuildFramework main class ######

class SConsBuildFramework :

	# Command-line options
	myCmdLineOptionsList			= ['debug', 'release', 'nodeps', 'deps', 'noexclude', 'exclude']
	myCmdLineOptions				= set( myCmdLineOptionsList )

	# sbf environment
	mySCONS_BUILD_FRAMEWORK			= ''
	mySbfLibraryRoot				= ''
	myVcs							= None

	# SCons environment
	myEnv							= None
	myCurrentLocalEnv				= None			# contains the lenv of the current project

	# Options instances
	mySBFOptions					= None
	myProjectOptions				= None

	# Global attributes from command line
	myBuildTargets					= set()
	#myGHasCleanOption				= False

	# Globals attributes
	myDate							= ''
	myDateTime						= ''
	myPlatform						= ''
	myCC							= ''			# cl, gcc
	myCCVersionNumber				= 0				# 8.000000 for cl8-0, 4.002001 for gcc 4.2.1
	myIsExpressEdition				= False			# True if Visual Express Edition, False otherwise
	myCCVersion						= ''			# cl8-0
	my_Platform_myCCVersion			= ''


	# Global attributes from .SConsBuildFramework.options or computed from it
	myNumJobs						= 1
	myCompanyName					= ''
	mySvnUrls						= []
	mySvnCheckoutExclude			= []
	mySvnUpdateExclude				= []
	myInstallPaths					= []
	myPublishPath					= ''
	myBuildPath						= ''
	mySConsignFilePath				= None
	myCachePath						= ''
	myCacheOn						= False
	myConfig						= ''
	myWarningLevel					= ''
	# Computed from .SConsBuildFramework.options
	myInstallExtPaths				= []
	myInstallDirectory				= ''
	myIncludesInstallPaths			= []
	myLibInstallPaths				= []
	myIncludesInstallExtPaths		= []
	myLibInstallExtPaths			= []
	myGlobalCppPath					= []
	myGlobalLibPath					= []

	#@todo use env and lenv or at least copy in env
	# Project local attributes from default.options
	myVcsUse						= ''
	myDefines						= []
	myType							= ''
	myVersion						= ''
	myPostfix						= ''
	myDeps							= []
	myUses							= []
	myLibs							= []
	myStdlibs						= []

	# Project local attributes
	myProjectPathName				= ''	# d:\Dev\SrcLib\vgsdk\dependencies\gle
	myProjectPath					= ''	# d:\Dev\SrcLib\vgsdk\dependencies
	myProject						= ''	# gle
	myProjectBuildPath				= ''
	myVersionMajor					= None
	myVersionMinor					= None
	myVersionMaintenance			= None
	myPostfixLinkedToMyConfig		= ''
	my_PostfixLinkedToMyConfig		= ''
	myFullPostfix					= ''
	my_FullPostfix					= ''
	myCxxFlags						= ''
	myCppPath						= []
	myLinkFlags						= ''
	myLibPath						= []

	myProjectBuildPathExpanded		= ''	# c:\temp\sbf\build\gle\0-3\win32\cl7-1\debug
	mySubsystemNotDefined			= None	# True if LINKFLAGS contains '/SUBSYSTEM:'

	# List of projects that have been already parsed by scons
	myFailedVcsProjects				= set()
	myParsedProjects				= {}
	myParsedProjectsSet				= set()




	###### Constructor ######
	def __init__( self ) :

		# Retrieves and normalizes SCONS_BUILD_FRAMEWORK
		self.mySCONS_BUILD_FRAMEWORK = os.getenv('SCONS_BUILD_FRAMEWORK')
		if self.mySCONS_BUILD_FRAMEWORK == None :
			raise SCons.Errors.UserError( "The SCONS_BUILD_FRAMEWORK environment variable is not defined." )
		self.mySCONS_BUILD_FRAMEWORK = getNormalizedPathname( os.getenv('SCONS_BUILD_FRAMEWORK') )

		# Sets the root directory of sbf library
		self.mySbfLibraryRoot = os.path.join( self.mySCONS_BUILD_FRAMEWORK, 'lib', 'sbf' )

		# Sets the vcs subsystem (at this time only svn is supported).
		self.myVcs = Subversion( self )

		# Reads .SConsBuildFramework.options from your home directory or SConsBuildFramework.options from $SCONS_BUILD_FRAMEWORK.
		homeSConsBuildFrameworkOptions = os.path.expanduser('~/.SConsBuildFramework.options')

		if os.path.isfile(homeSConsBuildFrameworkOptions) :
			# Reads from your home directory.
			self.mySBFOptions = self.readSConsBuildFrameworkOptions( homeSConsBuildFrameworkOptions )
		else :
			# Reads from $SCONS_BUILD_FRAMEWORK directory.
			self.mySBFOptions = self.readSConsBuildFrameworkOptions( os.path.join( self.mySCONS_BUILD_FRAMEWORK, 'SConsBuildFramework.options' ) )

		# Constructs SCons environment.
		tmpEnv = Environment( options = self.mySBFOptions )

		if tmpEnv['PLATFORM'] == 'win32' :
			# Tests existance of cl
			if len(tmpEnv['MSVS']['VERSIONS']) == 0 :
				print 'sbfError: no version of cl is available.'
				Exit( 1 )

			# Tests existance of the desired version of cl
			if tmpEnv['clVersion'] not in tmpEnv['MSVS']['VERSIONS'] and tmpEnv['clVersion'] != 'highest' :
				print 'sbfError: clVersion sets to', tmpEnv['clVersion'],
				if len(tmpEnv['MSVS']['VERSIONS']) == 1 :
					print ', available version is ', tmpEnv['MSVS']['VERSIONS']
				else :
					print ', available versions are ', tmpEnv['MSVS']['VERSIONS']
				Exit( 1 )

			# There is no more case of errors.
			if tmpEnv['clVersion'] == 'highest' :
				self.myEnv = tmpEnv
			else :
				self.myEnv = Environment( options = self.mySBFOptions, MSVS_VERSION = tmpEnv['clVersion'] )
				# TODO Environment is construct two times. This is done just to be able to read 'clVersion' option. OPTME see below :
				# env["MSVS"] = {"VERSION": "8.0"}
				# env["MSVS_VERSION"] = "8.0"
				# Tool("msvc")(env)

			pathFromEnv = os.environ['PATH'] ### FIXME not very recommended
			if pathFromEnv != None :
				self.myEnv['ENV']['PATH'] += pathFromEnv
			#print "self.myEnv['MSVS']", self.myEnv['MSVS']
			#print 'self.myEnv[MSVS_VERSION]', self.myEnv['MSVS_VERSION']
		else :
			self.myEnv = tmpEnv

		# Configures command line max length
		if self.myEnv['PLATFORM'] == 'win32' :
#			self.myEnv['MSVC_BATCH'] = True													# ?????????
			# @todo adds windows version helpers in sbf
			winVerTuple	= sys.getwindowsversion()
			winVerNumber= self.computeVersionNumber( [winVerTuple[0], winVerTuple[1]] )
			if winVerNumber >= 5.1 :
				# On computers running Microsoft Windows XP or later, the maximum length
				# of the string that you can use at the command prompt is 8191 characters.
				# XP version is 5.1
				self.myEnv['MAXLINELENGTH'] = 8191
				# On computers running Microsoft Windows 2000 or Windows NT 4.0,
				# the maximum length of the string that you can use at the command
				# prompt is 2047 characters.

		# Configures command line output
		if self.myEnv['printCmdLine'] == 'less' :
			self.myEnv['PRINT_CMD_LINE_FUNC'] = sbfPrintCmdLine
			if self.myEnv['PLATFORM'] == 'win32' :
				# cl prints always source filename. The following line (and 'PRINT_CMD_LINE_FUNC'), gets around this problem to avoid duplicate output.
				self.myEnv['CXXCOMSTR']		= 'sbfNull'
				self.myEnv['SHCXXCOMSTR']	= 'sbfNull'

				self.myEnv['RCCOMSTR'] = 'Compiling resource ${SOURCE.file}'
			else:
				self.myEnv['CXXCOMSTR']		= "$SOURCE.file"
				self.myEnv['SHCXXCOMSTR']	= "$SOURCE.file"

			self.myEnv['INSTALLSTR'] = "Installing ${SOURCE.file}"
		#self.myEnv['LINKCOMSTR'] = "Linking $TARGET"#'sbfLN'#print_cmd_line
		#self.myEnv['SHLINKCOMSTR'] = "Linking $TARGET"#'sbfShLN' #print_cmd_line
		#self.myEnv.Replace(LINKCOMSTR = "Linking... ${TARGET.file}")
		#self.myEnv.Replace(SHLINKCOMSTR = "$LINKCOMSTR")
		#self.myEnv.Replace(ARCOMSTR = "Creating archive... ${TARGET.file}")

# @todo uses UnknownVariables()
#		#
#		unknown = self.mySBFOptions.UnknownVariables()
#		print "Unknown variables:", unknown.keys()
#		if unknown:
#			print "Unknown variables:", unknown.keys()
#			Exit(1)

		# Analyses command line options
		AddOption(	"--weak-localext",
					action	= "store_true",
					dest	= "weak_localext",
					#default	= True,
					help	= "Disables SCons scanners for localExt directories." )

		AddOption(	"--no-weak-localext",
					action	= "store_false",
					dest	= "weak_localext",
					default	= True,
					help	= "See --weak-localext option" )

		# AddOption(	"--optimize",
					# type	= "int",
					# #action	= "store",
					# #dest	= "optimize",
					# default	= 1,
					# help	= "todo documentation" )
		#print self.myEnv.GetOption("optimize")
		#print self.myEnv.GetOption("weak_localext")
		#if self.myEnv.GetOption("optimize") == 0 :
		#	self.myEnv.SetOption("weak_localext", 0 )

		AddOption(	"--fast",
					action	= "store_true",
					#dest	= "fast",
					default	= False,
					help	= "todo documentation"
					)

		# @todo Each instance of '--verbose' on the command line increases the verbosity level by one, so if you need more details on the output, specify it twice.
		AddOption(	"--verbose",
					action	= "store_true",
					dest	= "verbosity",
					default	= False,
					help	= "Shows details about the results of running sbf. This can be especially useful when the results might not be obvious." )

#		print self.myEnv.Dump()

		# @todo FIXME : It is disabled, because it doesn't work properly
		# Log into a file the last scons outputs (stdout and stderr) for a project
		#myProject = os.path.basename( os.getcwd() )
		#logCommand = "tee " + os.path.join( env['buildPath'], myProject + "_sbf.log")
		#sys.stderr = sys.stdout = open( os.path.join( env['buildPath'], myProject + "_sbf.log"), 'w' )# or
		#sys.stdout = sys.stderr = os.popen(logCommand, "w")

		# myDate, myDateTime
		self.myDate		= str(datetime.date.today()).replace('-', '_')
		# format compatible with that specified in the RFC 2822 Internet email standard.
		self.myDateTime	= str(datetime.datetime.today().strftime("%a, %d %b %Y %H:%M:%S +0000"))

		# Prints sbf version, date and time at sbf startup
		if self.myEnv.GetOption('verbosity') :
			printSBFVersion()
			print 'started', self.myDateTime

		# Retrives all targets
		self.myBuildTargets = set( map(str, BUILD_TARGETS) )

		# Takes care of alias definition needed for command line options.
		mustAddAlias = True
		for target in self.myBuildTargets :
			if target not in self.myCmdLineOptions :
				mustAddAlias = False
				break

		Alias(		'all' )
		Default(	'all' )
		Alias( self.myCmdLineOptionsList )
		if mustAddAlias :
			Alias( self.myCmdLineOptionsList, 'all' )

		#self.myGHasCleanOption = env.GetOption('clean')

		# Sets clean=1 option if needed.
		if (	'clean' in self.myBuildTargets or
				'mrproper' in self.myBuildTargets	) :
			# target clean or mrproper
			buildTargetsWithoutCmdLineOptions = self.myBuildTargets - self.myCmdLineOptions

			if len(buildTargetsWithoutCmdLineOptions) != 1 :
				raise SCons.Errors.UserError(	"'clean' and 'mrproper' special targets must be used without any others targets.\nCurrent specified targets: %s"
												% convertToString(buildTargetsWithoutCmdLineOptions) )
			else :
				self.myEnv.SetOption('clean', 1)

		# Analyses command line options
		# and/or
		# Processes special targets used as shortcuts for sbf options
		# This 'hack' is useful to 'simulate' command-line options. But without '-' or '--'

		# Overrides the 'config' option, when one of the special targets, named 'debug' and 'release', is specified
		# at command line.
		if ('debug' in self.myBuildTargets) and ('release' in self.myBuildTargets) :
			raise SCons.Errors.UserError("Targets 'debug' and 'release' have been specified at command-line. Chooses one of both.")
		if 'debug' in self.myBuildTargets :
			self.myEnv['config'] = 'debug'
		elif 'release' in self.myBuildTargets :
			self.myEnv['config'] = 'release'

		# Overrides the 'nodeps' option, when one of the special targets is specified at command line.
		if ('nodeps' in self.myBuildTargets) and ('deps' in self.myBuildTargets) :
			raise SCons.Errors.UserError("Targets 'nodeps' and 'deps' have been specified at command-line. Chooses one of both.")
		if 'nodeps' in self.myBuildTargets :
			self.myEnv['nodeps'] = True
		elif 'deps' in self.myBuildTargets :
			self.myEnv['nodeps'] = False

		# Overrides the 'exclude' option, when one of the special targets is specified at command line.
		if ('noexclude' in self.myBuildTargets) and ('exclude' in self.myBuildTargets) :
			raise SCons.Errors.UserError("Targets 'noexclude' and 'exclude' have been specified at command-line. Chooses one of both.")
		if 'noexclude' in self.myBuildTargets :
			self.myEnv['exclude'] = False
		elif 'exclude' in self.myBuildTargets :
			self.myEnv['exclude'] = True


		# myPlatform, myCC, myCCVersionNumber, myCCVersion and my_Platform_myCCVersion
		# myPlatform = win32 | cygwin  | posix | darwin				TODO: TOTHINK: posix != linux and bsd ?, env['PLATFORM'] != sys.platform
		self.myPlatform	= self.myEnv['PLATFORM']

		# myCC, myCCVersionNumber, myCCVersion and my_Platform_myCCVersion
		if self.myEnv['CC'] == 'cl' :
			# Sets compiler
			self.myCC				=	'cl'
			# Extracts version number
			# Step 1 : Extracts x.y (without Exp if any)
			ccVersion				=	self.myEnv['MSVS_VERSION'].replace('Exp', '', 1)
			# Step 2 : Extracts major and minor version
			splittedCCVersion		=	ccVersion.split( '.', 1 )
			# Step 3 : Computes version number
			self.myCCVersionNumber = self.computeVersionNumber( splittedCCVersion )
			# Constructs myCCVersion ( clMajor-Minor[Exp] )
			self.myIsExpressEdition = self.myEnv['MSVS_VERSION'].find('Exp') != -1
			self.myCCVersion = self.myCC + self.getVersionNumberString2( self.myCCVersionNumber )
			if self.myIsExpressEdition :
				# Adds 'Exp'
				self.myCCVersion += 'Exp'
		elif self.myEnv['CC'] == 'gcc' :
			# Sets compiler
			self.myCC = 'gcc'
			# Extracts version number
			# Step 1 : Extracts x.y.z
			ccVersion				=	self.myEnv['CCVERSION']
			# Step 2 : Extracts major and minor version
			splittedCCVersion		=	ccVersion.split( '.', 2 )
			if len(splittedCCVersion) !=  3 :
				raise SCons.Errors.UserError( "Unexpected version schema for gcc compiler (expected x.y.z) : %s " % ccVersion )
			# Step 3 : Computes version number
			self.myCCVersionNumber = self.computeVersionNumber( splittedCCVersion[:2] )
			# Constructs myCCVersion ( gccMajor-Minor )
			self.myCCVersion = self.myCC + self.getVersionNumberString2( self.myCCVersionNumber )
		else :
			raise SCons.Errors.UserError( "Unsupported cpp compiler : %s" % self.myEnv['CC'] )

		self.my_Platform_myCCVersion = '_' + self.myPlatform + '_' + self.myCCVersion

		# Adds support of Microsoft Manifest Tool for Visual Studio 2005 (cl8) and up
		if self.myCC == 'cl' and self.myCCVersionNumber >= 8.000000 :
			self.myEnv['LINKCOM'	] = [self.myEnv['LINKCOM'	], 'mt /nologo -manifest ${TARGET}.manifest -outputresource:$TARGET;1']
			self.myEnv['SHLINKCOM'	] = [self.myEnv['SHLINKCOM'], 'mt /nologo -manifest ${TARGET}.manifest -outputresource:$TARGET;2']

		#
		if self.myEnv.GetOption('fast') :
			self.myEnv.Decider('MD5-timestamp')
		else :
			self.myEnv.Decider('MD5')

		#
		self.initializeGlobalsFromEnv( self.myEnv )

		# Initializes 'use' repository
		if UseRepository.isInitialized() == False :
			UseRepository.initialize( self )
			UseRepository.add( UseRepository.getAll() )

		# Generates help
		Help("""
Type:
 'scons sbfCheck' to check sbf and related tools installation.

 'scons svnAdd' to add files and directories used by sbf (i.e. all sources, configuration files and directory 'share').
 'scons svnCheckout'
 'scons svnCleanup'
 'scons svnStatus'
 'scons svnUpdate'

 'scons' or 'scons all' to build your project and all its dependencies in the current 'config' (debug or release). 'All' is the default target.
 'scons clean' to clean intermediate files (see buildPath option).
 'scons mrproper' to clean installed files (see installPaths option). 'clean' target is also executed, so intermediate files are cleaned.

 'scons vcproj' to build Microsoft Visual Studio project file(s).
 'scons vcproj_clean' or 'scons vcproj_mrproper'

 'scons dox' to generate doxygen documentation.
 'scons dox_clean' or 'scons dox_mrproper'

 'scons zipRuntime'
 'scons zipDeps'
 'scons zipPortable'
 'scons zipDev'
 'scons zipSrc'
 'scons zip'
 'scons nsis'


Command-line options:

debug      a shortcut for config=debug. See 'config' option for additionnal informations.
release    a shortcut for config=release. See 'config' option for additionnal informations.

nodeps     a shortcut for nodeps=true. See 'nodeps' option for additionnal informations.
deps       a shortcut for nodeps=false. See 'nodeps' option for additionnal informations.

noexclude  a shortcut for exclude=true. See 'exclude' option for additionnal informations.
exclude    a shortcut for exclude=false. See 'exclude' option for additionnal informations.


--weak-localext		Disables SCons scanners for localext directories.
--no-weak-localext	See --weak-localext

--verbose		Shows details about the results of running sbf. This can be especially useful when the results might not be obvious.
--fast			TODO



SConsBuildFramework options:
""")

#=======================================================================================================================
#	  'scons build' for all myproject_build
#	  'scons install' for all myproject_install
#
#	  'scons build' for all myproject_build
#	  'scons install' for all myproject_install
#	  'scons' or 'scons all' for all myproject (this is the default target)
#	  'scons debug' like target all, but config option is forced to debug
#	  'scons release' like target all but config option is forced to release
#	  'scons clean' for all myproject_clean
#	  'scons mrproper' for all myproject_mrproper
#
#	  'scons myproject_build' or 'myproject_install' or 'myproject' (idem myproject_install) or 'myproject_clean' or 'myproject_mrproper'
#
#     'scons myproject_vcproj' to build a Microsoft Visual Studio project file.
#=======================================================================================================================

		Help( self.mySBFOptions.GenerateHelpText(self.myEnv) )



	###### Initialize global attributes ######
	def initializeGlobalsFromEnv( self, lenv ) :

		# Updates myNumJobs, myCompanyName, mySvnUrls, mySvnCheckoutExclude and mySvnUpdateExclude
		self.myNumJobs				= lenv['numJobs']

		self.myCompanyName			= lenv['companyName']

		self.mySvnUrls				= lenv['svnUrls']
		self.mySvnCheckoutExclude	= lenv['svnCheckoutExclude']
		self.mySvnUpdateExclude		= lenv['svnUpdateExclude']

		self.myEnv.SetOption( 'num_jobs', self.myNumJobs )

		# Updates myInstallPaths, myInstallExtPaths and myInstallDirectory
		self.myInstallPaths = []
		for element in lenv['installPaths'] :
			self.myInstallPaths += [ getNormalizedPathname( element ) ]

		self.myInstallExtPaths = []
		for element in self.myInstallPaths :
			self.myInstallExtPaths	+= [element + 'Ext' + self.my_Platform_myCCVersion]

		if ( len(self.myInstallPaths) >= 1 ) :
			self.myInstallDirectory	= self.myInstallPaths[0]
		else :
			print 'sbfError: empty installPaths'
			Exit( 1 )

		# Updates myPublishPath
		self.myPublishPath = lenv['publishPath']

		# Updates myBuildPath, mySConsignFilePath, myCachePath, myCacheOn, myConfig and myWarningLevel
		self.myBuildPath = getNormalizedPathname( lenv['buildPath'] )

		# SCons signatures configuration (i.e. location of .sconsign file)
		if lenv['SConsignFilePath'] == 'buildPath' :
			# Explicitly stores signatures in directory given by 'buildPath' option in a file named '.sconsign.dblite'
			self.mySConsignFilePath = self.myBuildPath
		else :
			# Explicitly stores signatures in directory given by 'SConsignFilePath' option in a file named '.sconsign.dblite'
			self.mySConsignFilePath = getNormalizedPathname( lenv['SConsignFilePath'] )

		if not os.path.isabs( self.mySConsignFilePath ) :
			print 'sbfError: SConsignFilePath option = %s' % self.mySConsignFilePath
			print 'sbfError: SConsignFilePath option is not an absolute path name.'
			Exit(1)

		self.myEnv.SConsignFile( os.path.join(self.mySConsignFilePath, '.sconsign') )

		self.myCachePath	= getNormalizedPathname( lenv['cachePath'] )
		self.myCacheOn		= lenv['cacheOn']
		if (self.myCacheOn == True) and \
		(len( self.myCachePath ) > 0 ) :
			lenv.CacheDir( self.myCachePath )
			if lenv.GetOption('verbosity') :
				print 'sbfInfo: Use cache ', self.myCachePath
		else :
			if lenv.GetOption('verbosity') :
				print 'sbfInfo: Don\'t use cache'

		self.myConfig		= lenv['config']
		self.myWarningLevel	= lenv['warningLevel']

		### use myInstallPaths and myInstallExtPaths to update myIncludesInstallPaths, myLibInstallPaths,
		### myIncludesInstallExtPaths, myLibInstallExtPaths, myGlobalCppPath and myGlobalLibPath
		for element in self.myInstallPaths :
			self.myIncludesInstallPaths	+=	[ os.path.join(element, 'include') ]
			self.myLibInstallPaths		+=	[ os.path.join(element, 'lib') ]

		for element in self.myInstallExtPaths :
			self.myIncludesInstallExtPaths	+=	[ os.path.join(element, 'include') ]
			self.myLibInstallExtPaths		+=	[ os.path.join(element, 'lib') ]

		#
		if self.myEnv.GetOption('weak_localext') :
			self.myGlobalCppPath = self.myIncludesInstallPaths
			for element in self.myIncludesInstallExtPaths :
				self.myEnv.Append( CCFLAGS = ['-I' + element] )
		else :
			self.myGlobalCppPath = self.myIncludesInstallPaths + self.myIncludesInstallExtPaths

		self.myGlobalLibPath = self.myLibInstallPaths + self.myLibInstallExtPaths

		# ???
		#goFast = False
		#if goFast == True :
			#self.myEnv.SetOption('max_drift', 1)
			#self.myEnv.SetOption('implicit_cache', 1)
			#print os.getenv('NUMBER_OF_PROCESSORS')



	###### Initialize project from lenv ######
	def initializeProjectFromEnv( self, lenv ) :
		self.myVcsUse	= lenv['vcsUse']
		self.myDefines	= lenv['defines']
		self.myType		= lenv['type']
		self.myVersion	= lenv['version']
		self.myPostfix	= lenv['postfix']
		self.myDeps		= lenv['deps']
		self.myUses		= lenv['uses']
		self.myLibs		= lenv['libs']
		self.myStdlibs	= lenv['stdlibs']



	###### Initialize project ######
	def initializeProject( self, projectPathName ) :

		# Already done in method buildProject(), but must be redone (because of recursiv call to buildProject())
		self.myProjectPathName	= projectPathName
		self.myProjectPath		= os.path.dirname( projectPathName )
		self.myProject			= os.path.basename(projectPathName)

		if ( os.path.isabs(self.myBuildPath) ) :
			self.myProjectBuildPath = self.myBuildPath
		else :
			self.myProjectBuildPath = os.path.join( self.myProjectPathName, self.myBuildPath )

		# processes myVersion
		splittedVersion = self.myVersion.split( '-' )
		if len(splittedVersion) not in [2, 3] :
			raise SCons.Errors.UserError("In project configuration file, 'version' must used the following schemas : major-minor or major-minor-maintenance\nCurrent specified version: %s" % self.myVersion )
		self.myVersionMajor = int(splittedVersion[0])
		self.myVersionMinor = int(splittedVersion[1])
		if len(splittedVersion) == 3 :
			self.myVersionMaintenance = int(splittedVersion[2])
		else :
			self.myVersionMaintenance = 0

		if ( self.myConfig == 'debug' ) :										### TODO: not good if more than one config must be built
			self.myPostfixLinkedToMyConfig = 'D'
			self.my_PostfixLinkedToMyConfig = '_' + self.myPostfixLinkedToMyConfig
		else : # release
			self.myPostfixLinkedToMyConfig = ''
			self.my_PostfixLinkedToMyConfig = ''

		if ( len(self.myPostfix) > 0 ) :
			self.myFullPostfix = self.myPostfix + self.my_PostfixLinkedToMyConfig
		else :
			self.myFullPostfix = self.myPostfixLinkedToMyConfig

		#@todo function to add '_' if not empty
		if ( len(self.myFullPostfix) > 0 ) :
			self.my_FullPostfix = '_' + self.myFullPostfix
		else :
			self.my_FullPostfix = ''

		###
		self.myCxxFlags		= ''
		self.myCppPath		= [os.path.join(self.myProjectPathName, 'include')] + self.myGlobalCppPath
		self.myLinkFlags	= ''
#		print 'A:projectPathName', projectPathName
#		print 'A:self.myLibPath init=', self.myLibPath
#		print 'A:self.myGlobalLibPath=', self.myGlobalLibPath
		self.myLibPath		= self.myGlobalLibPath
#		print 'B:self.myLibPath init=', self.myLibPath
#		print 'B:self.myGlobalLibPath=', self.myGlobalLibPath



	###### Reads the main configuration file (i.e. configuration of sbf) ######
	# @todo
	def readSConsBuildFrameworkOptions( self, file ) :

		myOptions = Variables( file )
		myOptions.AddVariables(
			BoolVariable(	'nodeps', "Sets to true, i.e. y, yes, t, true, 1, on and all, to do not follow project dependencies. Sets to false, i.e. n, no, f, false, 0, off and none, to follow project dependencies.",
							'false' ),
			BoolVariable(	'exclude', "Sets to true, i.e. y, yes, t, true, 1, on and all, to use the 'projectExclude' sbf option. Sets to false, i.e. n, no, f, false, 0, off and none, to ignore the 'projectExclude' sbf option.",
							'true' ),

			('numJobs', 'Allow N jobs at once. N must be an integer equal at least to one.', 1 ),
			('outputLineLength', 'Sets the maximum length of one single line printed by sbf.', 79 ),
			EnumVariable(	'printCmdLine', "Sets to 'full' to print all command lines launched by sbf, and sets to 'less' to hide command lines and see only a brief description of each command.",
							'less',
							allowed_values = ( 'full', 'less' ) ), # @todo silent

			('companyName', 'Sets the name of company that produced the project. This is used on win32 platform to embedded in exe, dll or lib files additional informations.', '' ),

			('pakPaths', "Sets the list of paths from which packages can be obtained. No matter what is specified by this options, the first implicit path where packages are searched would be 'installPaths[0]/sbfPak'.", [] ),

			('svnUrls', 'The list of subversion repositories used, from first to last, until a successful checkout occurs.', []),
			('projectExclude', 'The list of projects excludes from any sbf operations. All projects not explicitly excluded will be included. The project from which sbf was initially invoked is never excluded.', []),
			('weakLocalExtExclude', 'The list of packages (see \'uses\' project option for a complete list of available packages) excludes by the --weak-localext option.'
			' --weak-localext could be used to disables SCons scanners for localExt directories.'
			' All packages not explicitly excluded will be included.', []),
			('svnCheckoutExclude', 'The list of projects excludes from subversion checkout operations. All projects not explicitly excluded will be included.', []),
			('svnUpdateExclude', 'The list of projects excludes from subversion update operations. All projects not explicitly excluded will be included.', []),

			EnumVariable(	'clVersion', 'MS Visual C++ compiler (cl.exe) version using the following version schema : x.y or year. Use the special value \'highest\' to select the highest installed version.',
							'highest',
							allowed_values = ( '7.1', '8.0Exp', '8.0', 'highest' ),
							map={
									'2003'		: '7.1',
									'2005Exp'	: '8.0Exp',
									'2005'		: '8.0',
									} ),

			('installPaths', 'The list of search paths to \'/usr/local\' like directories. The first one would be used as a destination path for target named install.', []),

			('publishPath', 'The result of a target, typically copied in installPaths[0], could be transfered to another host over a remote shell using rsync. This option sets the destination of publishing (see rsync for destination syntax).', ''),
			BoolVariable('publishOn', 'Sets to True to enabled the publishing. See \'publishPath\' option for additional informations.', False),

			PathVariable(	'buildPath',
							'The build directory in which to build all derived files. It could be an absolute path, or a relative path to the project being build)',
							'build',
							PathVariable.PathAccept),
			(	'SConsignFilePath',
				'Stores signatures (.sconsign.dblite file) in the specified absolute path name. If SConsignFilePath is not defined or is equal to string \'buildPath\' (the default value), the value of \'buildPath\' option is used.',
				'buildPath' ),
			PathVariable('cachePath', 'The directory where derived files will be cached. The derived files in the cache will be shared among all the builds using the same cachePath directory.', '', PathVariable.PathAccept),
			BoolVariable('cacheOn', 'Sets to True to use the build cache system (see cachePath option), False (the default) to disable it.', False),

			EnumVariable(	'config', "Sets to 'release' to build the production program/library. Or sets to 'debug' to build the debug version.",
							'release',
							allowed_values=('debug', 'release'),
							map={}, ignorecase=1 ),
			EnumVariable(	'warningLevel', 'Sets the level of warnings.', 'normal',
							allowed_values=('normal', 'high'),
							map={}, ignorecase=1 )
								)
#		unknown = myOptions.UnknownVariables()
#		print "Unknown variables:", unknown.keys()
		return myOptions


	###### Reads a configuration file for a project ######
	# @todo
	def readProjectOptions( self, file ) :

		myOptions = Variables( file )
		myOptions.AddVariables(
			('description', "Description of the project to be presented to users. This is used on win32 platform to embedded in exe, dll or lib files additional informations.", '' ),

			EnumVariable(	'vcsUse', "'yes' if the project use a versioning control system, 'no' otherwise.", 'yes',
							allowed_values=('yes', 'no'),
							map={}, ignorecase=1 ),

			('defines', 'The list of preprocessor definitions given to the compiler at each invocation (same effect as #define xxx).', ''),
			EnumVariable(	'type', "Specifies the project/target type. 'exec' for executable projects, 'static' for static library projects, 'shared' for dynamic library projects, 'none' for meta or headers only projects.",
							'none',
							allowed_values=('exec', 'static','shared','none'),
							map={}, ignorecase=1 ),
			('version', "Sets the project version. The following version schemas must be used : major-minor or major-minor-maintenance. For example '1-0' or '1-0-1'", '0-0'),
			('postfix', 'Adds a postfix to the target name.', ''),

			('deps', 'Specifies list of dependencies to others projects. Absolute path is forbidden.', []),

			(	'uses',
				'Specifies a list of packages to configure for compilation and link stages.\nAvailable packages:%s\nAlias: %s' %
				(convertToString(UseRepository.getAllowedValues()), convertDictToString(UseRepository.getAlias())),
				[],
				usesValidator,
				usesConverter ),

			('libs', 'The list of libraries used during the link stage that have been compiled with SConsBuildFramework (this SCons system).', []),
			('stdlibs', 'The list of standard libraries used during the link stage.', [])
								)

		return myOptions


	###### Reads a configuration file for a project ######
	###### Updates environment (self.myProjectOptions and lenv are modified).
	# Returns true if config file exists, false otherwise.
	def readProjectOptionsAndUpdateEnv( self, lenv, configDotOptionsFile = 'default.options' ) :
		configDotOptionsPathFile = self.myProjectPathName + os.sep + configDotOptionsFile
		retVal = os.path.isfile(configDotOptionsPathFile)
		if retVal :
			# update lenv with config.options
			self.myProjectOptions = self.readProjectOptions( configDotOptionsPathFile )
			self.myProjectOptions.Update( lenv )
		return retVal



	###### Configures CxxFlags & LinkFlags ######
	def configureCxxFlagsAndLinkFlagsOnWin32( self, lenv ) :

		# Configures Microsoft Platform SDK for Windows Server 2003 R2 (TODO: FIXME : should be done by SCons...)
		if self.myIsExpressEdition :
			#print 'self.myCppPath=', self.myCppPath
			if lenv.GetOption('weak_localext') :
				lenv.Append( CCFLAGS = ['-IC:\\Program Files\\Microsoft Platform SDK for Windows Server 2003 R2\\Include'] )
			else :
				lenv.Append( CPPPATH = 'C:\\Program Files\\Microsoft Platform SDK for Windows Server 2003 R2\\Include' )
			#self.myCppPath.append( 'C:\\Program Files\\Microsoft Platform SDK for Windows Server 2003 R2\\Include' )
			#print 'self.myCppPath=', self.myCppPath
			lenv.Append( LIBPATH = 'C:\\Program Files\\Microsoft Platform SDK for Windows Server 2003 R2\\Lib' )

		#
		if self.myCCVersionNumber >= 8.000000 :
			self.myCxxFlags += ' /EHsc '			# /GX is deprecated in Visual C++ 2005
		elif self.myCCVersionNumber >= 7.000000 :
			self.myCxxFlags += ' /GX '
			if self.myConfig == 'release' :
				self.myCxxFlags += ' /Zm600 '

		# /TP : Specify Source File Type (C++) => adds by SCons
		# /GR : Enable Run-Time Type Information
		self.myCxxFlags += ' /GR '
		# Defines
		self.myCxxFlags += ' /DWIN32 /D_WINDOWS /DNOMINMAX '

		if self.myConfig == 'release' :							### TODO: use /Zd in release mode to be able to debug a little.
			self.myCxxFlags += ' /DNDEBUG '
			self.myCxxFlags += ' /MD /O2 '
		else :
			self.myCxxFlags += ' /D_DEBUG /DDEBUG '
			# /Od : Disable (Debug)
			self.myCxxFlags += ' /MDd /Od '
			lenv.AppendUnique( CXXFLAGS = '/Z7' )
			lenv.AppendUnique( LINKFLAGS = '/DEBUG' )
			# /Zi : Produces a program database (PDB) that contains type information and symbolic debugging information
			# for use with the debugger. The symbolic debugging information includes the names and types of variables,
			# as well as functions and line numbers. Using the /Zi instead may yield improved link-time performance,
			# although parallel builds will no longer work. You can generate PDB files with the /Zi switch by overriding
			# the default $CCPDBFLAGS variable
			# /ZI : Produces a program database in a format that supports the Edit and Continue feature.
			# /Gm : Enable Minimal Rebuild.
			#self.myCxxFlags += ' /ZI /Gm ' TODO not compatible with parallel (-j) builds.

		# Warnings
		if self.myWarningLevel == 'normal' :		### TODO: it is dependent of the myConfig. Must be changed ? yes, do it...
			self.myCxxFlags += ' /W3 '
		else :
			#
			self.myCxxFlags += ' /W4 '
			# /Wall : Enables all warnings
			self.myCxxFlags += ' /Wall '
			#
#			if self.myCCVersionNumber >= 7.000000 :
				# /Wp64 : Detect 64-Bit Portability Issues
#				self.myCxxFlags += ' /Wp64 '

		# Subsystem and incremental flags
		self.mySubsystemNotDefined = str(lenv['LINKFLAGS']).upper().find( '/SUBSYSTEM:' ) == -1
		if self.myConfig == 'release' :
			# subsystem sets to console to output debugging informations.
			if self.mySubsystemNotDefined :
				lenv.Append( LINKFLAGS = ['/SUBSYSTEM:CONSOLE'] )
			#self.myLinkFlags	+= ' /SUBSYSTEM:CONSOLE '
			#self.myLinkFlags	+= ' /SUBSYSTEM:WINDOWS '

			# To ensure that the final release build does not contain padding or thunks, link nonincrementally.
			self.myLinkFlags += ' /INCREMENTAL:NO '
		else :
			# subsystem sets to console to output debugging informations.
			if self.mySubsystemNotDefined :
				lenv.Append( LINKFLAGS = ['/SUBSYSTEM:CONSOLE'] )

			# By default, the linker runs in incremental mode.
#===============================================================================
#
#		# TODO: FIXME: hack for boost
#		self.myCxxFlags		+= ' /DBOOST_ALL_DYN_LINK '
#===============================================================================

		# self.myLinkFlags	+= ' /VERSION:%s ' % self.myVersion.replace('-','.')	TODO: use a .def file
		if		self.myType == 'exec' :
			# /GA : Results in more efficient code for an .exe file for accessing thread-local storage (TLS) variables.
			self.myCxxFlags += ' /GA '
		elif	self.myType == 'shared' :
			self.myCxxFlags	+= ' /D_USRDLL '



	def configureCxxFlagsAndLinkFlagsOnPosix( self, lenv ) :

		lenv['CXX'] = lenv.WhereIs('g++')											### FIXME: remove me
																					### myCxxFlags += ' -pedantic'
		if ( self.myConfig == 'release' ) :
			self.myCxxFlags	+= ' -DNDEBUG -O3 '										### TODO: more compiler and cpu optimizations
		else :
			self.myCxxFlags	+= ' -D_DEBUG -DDEBUG -g -O0 '							### profiling myCxxFlags += ' -pg', mpatrol, leaktracer

		# process myWarningLevel, adds always -Wall option.							TODO: adds more warnings with myWarningLevel = 'high' ?
		self.myCxxFlags	+= ' -Wall '


	def configureCxxFlagsAndLinkFlags( self, lenv ) :

		### TODO: moves defines(-Dxxxx) from platform specific methods into this one.
		### Completes myCxxFlags and myLinkFlags ###
		if ( self.myPlatform == 'win32' ) :
			self.configureCxxFlagsAndLinkFlagsOnWin32( lenv )
		elif ( self.myPlatform == 'cygwin' or self.myPlatform == 'posix' ) :
			self.configureCxxFlagsAndLinkFlagsOnPosix( lenv )
		else:
			raise SCons.Errors.UserError("Unknown platform %s." % self.myPlatform)

		# Completes myCxxFlags with some defines
		if ( self.myType == 'shared' ) :
			self.myCxxFlags += ' -D' + self.myProject.upper() + '_EXPORTS '

		if ( sys.platform == 'darwin' ) :
			self.myCxxFlags += ' -D__MACOSX__'
		elif ( string.find( sys.platform, 'linux' ) != -1 ) :
			self.myCxxFlags += ' -D__linux'



	def vcsOperation( self, lenv, vcsOperation, opDescription ) :

		# Checks if vcs operation of this project has already failed
		if self.myProject not in self.myFailedVcsProjects :
			#print
			print stringFormatter( lenv, "vcs %s project %s in %s" % (opDescription, self.myProject, self.myProjectPath) )

			successful = vcsOperation( self.myProjectPathName, self.myProject )

			if not successful :
				self.myFailedVcsProjects.add( self.myProject )
				print "sbfWarning: Unable to do vcs operation in directory", self.myProjectPathName
			#else vcs operation successful.
			print
			return successful
		else:
			print
			return False


	def vcsAdd( self, lenv ):
		return self.vcsOperation( lenv, self.myVcs.add, 'add' )

	def vcsCheckout( self, lenv ):
		opDescription = 'checkout'
		# Checks if this project must skip vcs operation
		if self.myProject in self.mySvnCheckoutExclude :
			if lenv.GetOption('verbosity') :
				print stringFormatter( lenv, "vcs %s project %s in %s" % (opDescription, self.myProject, self.myProjectPath) )
				print "sbfInfo: Exclude from vcs %s." % opDescription
				print "sbfInfo: Skip to the next project..."
				print
			return
		else:
			return self.vcsOperation( lenv, self.myVcs.checkout, opDescription )

	def vcsCleanup( self, lenv ):
		return self.vcsOperation( lenv, self.myVcs.cleanup, 'cleanup' )

	def vcsStatus( self, lenv ):
		return self.vcsOperation( lenv, self.myVcs.status, 'status' )

	def vcsUpdate( self, lenv ):
		opDescription = 'update'
		# Checks if this project must skip vcs operation
		if self.myProject in self.mySvnUpdateExclude :
			if lenv.GetOption('verbosity') :
				print stringFormatter( lenv, "vcs %s project %s in %s" % (opDescription, self.myProject, self.myProjectPath) )
				print "sbfInfo: Exclude from vcs %s." % opDescription
				print "sbfInfo: Skip to the next project..."
				print
			return
		else:
			return self.vcsOperation( lenv, self.myVcs.update, opDescription )



	###### Build a project ######
	def buildProject( self, projectPathName ) :

		# Normalizes incoming path
		projectPathName = getNormalizedPathname( projectPathName )

		# Initializes basic informations about incoming project
		self.myProjectPathName	= projectPathName
		self.myProjectPath		= os.path.dirname(	self.myProjectPathName	)
		self.myProject			= os.path.basename(	self.myProjectPathName	)

		# Tests if the incoming project must be ignored
		if self.myEnv['exclude'] and \
		   (self.myProject in self.myEnv['projectExclude']) and \
		   (self.myProject != os.path.basename(GetLaunchDir())) :
			if self.myEnv.GetOption('verbosity') :
				print "Ignore project %s in %s" % (self.myProject, self.myProjectPath)
			return

		# User wants a vcs status ?
		tryVcsStatus = ('svnStatus' in self.myBuildTargets) or (self.myProject+'_svnStatus' in self.myBuildTargets)

		# User wants a vcs checkout ?
		tryVcsCheckout = ('svnCheckout' in self.myBuildTargets) or (self.myProject+'_svnCheckout' in self.myBuildTargets)

		# Checks validity of 'svnUrls' option (only if needed).
		if tryVcsCheckout and len(self.mySvnUrls) == 0 :
			raise SCons.Errors.UserError("Unable to do any svn checkout, because option 'svnUrls' is empty.")

		# Tests existance of project path name
		existanceOfProjectPathName = os.path.isdir(self.myProjectPathName)

		# Configures a new environment
		self.myCurrentLocalEnv = self.myEnv.Clone()
		lenv = self.myCurrentLocalEnv

		# What must be done for this project ?
		#existanceOfProjectPathName	tryVcsCheckout		action
		#True						True 				env (checkout and env, if lenv['vcsUse'] == 'yes' and not already checkout from vcs)
		#True						False				env
		#False						True				vcsCheckout env
		#False						False				return

		if not existanceOfProjectPathName :
			if not tryVcsCheckout:
				print stringFormatter( lenv, "project %s in %s" % (self.myProject, self.myProjectPath) )
				print "sbfWarning: Unable to find project", self.myProject, "in directory", self.myProjectPath
				print "sbfInfo: None of targets svnCheckout or", self.myProject + "_svnCheckout have been specified."
				self.myFailedVcsProjects.add( self.myProject )
				return
			else :
				self.vcsCheckout( lenv )
		else:
			successful = self.readProjectOptionsAndUpdateEnv( lenv )
			if successful :
				if tryVcsCheckout :
					if lenv['vcsUse'] == 'yes' :
						projectURL = self.myVcs.getUrl( self.myProjectPathName )
						if len(projectURL) > 0 :
							# @todo only if verbose
							print stringFormatter( lenv, "project %s in %s" % (self.myProject, self.myProjectPath) )
							print "sbfInfo: Already checkout from %s using svn." % projectURL
							print "sbfInfo: Uses 'svnUpdate' to get the latest changes from the repository."
							print
						else:
							self.vcsCheckout( lenv )
					else:
						if lenv.GetOption('verbosity') :
							print "Skip project %s in %s" % (self.myProject, self.myProjectPath)
							print
						# @todo only if verbose
						#print "----------------------- project %s in %s -----------------------" % (self.myProject, self.myProjectPath)
						#print "sbfInfo: 'vcsUse' option sets to no. So svn checkout is disabled."
				elif tryVcsStatus and lenv['vcsUse'] == 'yes' : # @todo moves lenv['vcsUse'] == 'yes' test in vcsOperation ?
					self.vcsStatus( lenv )
			#else nothing to do

		# Tests existance of project path name
		if os.path.isdir(self.myProjectPathName) :
			successful = self.readProjectOptionsAndUpdateEnv( lenv )
			if successful :
				# Adds the new environment
				self.myParsedProjects[self.myProject] = lenv
				self.myParsedProjectsSet.add( self.myProject.lower() )
			else:
				raise SCons.Errors.UserError("Unable to find 'default.options' file for project %s in directory %s." % (self.myProject, self.myProjectPath) )
		else:
			print "sbfWarning: Unable to find project", self.myProject, "in directory", self.myProjectPath
			print "sbfInfo: Skip to the next project..."
			self.myFailedVcsProjects.add( self.myProject )
			return

#===============================================================================
#		# a vcs add ?
#		tryVcsAdd = 'svnAdd' in self.myBuildTargets
#
#		if tryVcsAdd :
#			if lenv['vcsUse'] == 'yes' :	# @todo moves this test in vcsOperation
#				self.vcsAdd( lenv )
#			else:
#				if lenv.GetOption('verbosity') :
#					print "Skip project %s in %s" % (self.myProject, self.myProjectPath)
#===============================================================================

		# User wants a vcs update ?
		tryVcsUpdate = ('svnUpdate' in self.myBuildTargets) or (self.myProject+'_svnUpdate' in self.myBuildTargets)

		if tryVcsUpdate :
			if lenv['vcsUse'] == 'yes' :
				self.vcsUpdate( lenv )
				self.readProjectOptionsAndUpdateEnv( lenv )
			else:
				if lenv.GetOption('verbosity') :
					print "Skip project %s in %s" % (self.myProject, self.myProjectPath)
				# @todo only if verbose
				#print "----------------------- project %s in %s -----------------------" % (self.myProject, self.myProjectPath)
				#print "sbfInfo: 'vcsUse' option sets to no. So svn update is disabled."
		# else nothing to do.

		# Tests project options existance
		if self.myProjectOptions is None :
			# No project options, this is not a project to build.
			return

		# Constructs dependencies
		# @todo only in debug
		#print "sbfDebug:%s dependencies are %s" % (self.myProject, lenv['deps'])

		# Adds help on project options only for the first project.
		if len(self.myParsedProjects) == 1 :
			Help("""


%s options:
""" % self.myProject )
			Help( self.myProjectOptions.GenerateHelpText(lenv) )

		# Takes care of 'nodeps' option
		if lenv['nodeps'] :
			# Removes all dependencies because 'nodeps' option is enabled
			del lenv['deps'][:]
		else:
# @todo FIXME: Automatic building of sbf library is disabled, because it affects badly zip and nsis targets.
			# Builds sbf library
#			if 'sbf' not in self.myParsedProjectsSet:
				# sbf not already "build"
				#print ('buildProject %s' % self.mySbfLibraryRoot)
#				self.buildProject( self.mySbfLibraryRoot )

			# Builds deps (i.e. dependencies)
			for dependency in lenv['deps']:
				if os.path.isabs( dependency ):
					# dependency is an absolute path
					raise SCons.Errors.UserError("Absolute path is forbidden in 'deps' project option.")

				# dependency is a path relative to default.options file directory
				normalizedDependency			= getNormalizedPathname( projectPathName + os.sep + dependency )
				incomingProjectName				= os.path.basename(normalizedDependency)
				lowerCaseIncomingProjectName	= incomingProjectName.lower()
				if	lowerCaseIncomingProjectName not in self.myParsedProjectsSet :
					# dependency not already "build"
					#print ('buildProject %s' % normalizedDependency)
					if incomingProjectName not in self.myFailedVcsProjects :
						self.buildProject( normalizedDependency )
					#else: nothing to do
				else:
					# A project with the same name (without taking case into account) has been already parsed.
					if incomingProjectName not in self.myParsedProjects :
						# A project with the same name has been already parsed, but with a different case
						registeredProjectName = None
						for project in self.myParsedProjects :
							if project.lower() == incomingProjectName.lower() :
								raise SCons.Errors.UserError("The dependency %s, defined in project %s, has already been encountered with a different character case (%s). It's forbidden." % (normalizedDependency, lenv['sbf_projectPathName'], self.myParsedProjects[project]['sbf_projectPathName'] ) )
						else:
							# Must never happened
							raise SCons.Errors.UserError("Internal sbf error.")
					else:
						# A project with the same name has been already parsed (with the same case).
						parsedProject = self.myParsedProjects[ incomingProjectName ]
						# Checks path ?
						if parsedProject['sbf_projectPathName'] != normalizedDependency :
							raise SCons.Errors.UserError("Encountered the following two projects :\n%s and \n%s\nwith the same name (without taking case into account). It's forbidden." % (parsedProject['sbf_projectPathName'], normalizedDependency) )
						#else: nothing to do (because same path => project already parsed).
							#print "sbfDebug: project %s already parsed." % projectPathName

		# initialize the project
		self.initializeProjectFromEnv( lenv )
		self.initializeProject( projectPathName )

#=======================================================================================================================
#		# Sets clean=1 option if needed.
#		if (	('clean' in self.myBuildTargets)						or
#				('mrproper' in self.myBuildTargets)						or
#				(self.myProject + '_clean' in self.myBuildTargets)		or
#				(self.myProject + '_mrproper' in self.myBuildTargets ) ) :
#			lenv.SetOption('clean', 1)
#=======================================================================================================================

		# used by code printing messages during the different build stage.
		lenv['sbf_projectPathName'	] = self.myProjectPathName
		lenv['sbf_projectPath'		] = self.myProjectPath
		lenv['sbf_project'			] = self.myProject

		if tryVcsCheckout or tryVcsUpdate :
#			print "skip"
			return
#		print 'initializeProject %s' % projectPathName

		# @todo Finds a better place to do that
		lenv['sbf_version_major']		= self.myVersionMajor
		lenv['sbf_version_minor']		= self.myVersionMinor
		lenv['sbf_version_maintenance']	= self.myVersionMaintenance

		#lenv['sbf_projectPathName'] = projectPathName
		#print "self.myProjectPathName==projectPathName?", self.myProjectPathName, "\n", projectPathName

		os.chdir( projectPathName )																				### FIXME is chdir done at scons level ?
		# Dumping construction environment (for debugging).														# TODO : a method printDebugInfo()
		#lenv.Dump()
		#print 'DEBUG:cwd=', os.getcwd()

		### construct project ###
		#print "sbfDebug: Constructing project %s in %s" % (self.myProject, self.myProjectPathName)

		### expand myProjectBuildPathExpanded
		self.myProjectBuildPathExpanded = os.path.join( self.myProjectBuildPath, self.myProject, self.myVersion, self.myPlatform, self.myCCVersion, self.myConfig )

		if ( len(self.myPostfix) > 0 ) :
			self.myProjectBuildPathExpanded += '_' + self.myPostfix

		### configure myCxxFlags with myDefines
		for define in self.myDefines :
			self.myCxxFlags	+=	' -D' + define + ' '

		# Adds to command-line several defines with version number informations.

		lenv.AppendUnique( CPPDEFINES = [ ("MODULE_NAME",		"\\\"%s\\\"" % self.myProject ) ] )
		lenv.AppendUnique( CPPDEFINES = [ ("MODULE_VERSION",	"\\\"%s\\\"" % self.myVersion ) ] )
		lenv.AppendUnique( CPPDEFINES = [ ("MODULE_MAJOR_VER",	"%s" % self.myVersionMajor ) ] )
		lenv.AppendUnique( CPPDEFINES = [ ("MODULE_MINOR_VER",	"%s" % self.myVersionMinor ) ] )
		lenv.AppendUnique( CPPDEFINES = [ ("MODULE_MAINT_VER",	"%s" % self.myVersionMaintenance ) ] )

		### configure compiler and linker flags.
		self.configureCxxFlagsAndLinkFlags( lenv )

		###### configure environment ######
		#print 'before=', lenv['LIBPATH']
#		print '1:self.myLibPath=', self.myLibPath
#		if lenv.has_key( 'LIBPATH' ) :
#			print '1=LIBPATH', lenv['LIBPATH']
		lenv.Append(	CXXFLAGS	= self.myCxxFlags )
		lenv.AppendUnique( CPPPATH = self.myCppPath )
		lenv.Append(	LINKFLAGS	= self.myLinkFlags,
						LIBPATH		= self.myLibPath ) # @todo AppendUnique should be better, but seems to cut cmd-line
#		print '2:self.myLibPath=', self.myLibPath
#		print '2=LIBPATH', lenv['LIBPATH']

# @todo
		# configure lenv['LIBS'] with sbf library
#		sbfLibraryName = 'sbf_0-0' + self.my_Platform_myCCVersion + self.my_PostfixLinkedToMyConfig
#		lenv.AppendUnique( LIBS = [sbfLibraryName] ) # @todo

		# configure lenv['LIBS'] with lenv['stdlibs']
		lenv.Append( LIBS = lenv['stdlibs'] ) # @todo AppendUnique

		# configure lenv['LIBS'] with lenv['libs']
		for lib in lenv['libs'] :
			libSplited	= string.split(lib, ' ')					# @todo see UseRepository.extract()
			libExpanded = ''
			if ( len(libSplited) == 1 ) :
				libExpanded += lib + self.my_Platform_myCCVersion + self.my_PostfixLinkedToMyConfig
			elif ( len(libSplited) == 2 ) :
				libExpanded += libSplited[0] + '_' + libSplited[1] + self.my_Platform_myCCVersion + self.my_PostfixLinkedToMyConfig
			else:
				print 'sbfWarning: skip ', lib, ' because its name contains more than two spaces'

			lenv.Append( LIBS = [libExpanded] )

		# Configures lenv[*] with lenv['uses']
		uses( self, lenv, lenv['uses'] )
		usesAlreadyConfigured = set( lenv['uses'] )

		# Configures lenv[*] with lenv['uses'] from dependencies
		allDependencies = self.getAllDependencies( lenv )
	#	print 'project', self.myProject
	#	print 'uses', lenv['uses']
	#	print 'dependencies', lenv['deps']
	#	print "recursiveDependencies:", allDependencies

		# Computes union of 'uses' option for all dependencies
		usesSet = set()
		for dependency in allDependencies:
			dependencyEnv = self.myParsedProjects[ dependency ]
			usesSet = usesSet.union( set(dependencyEnv['uses']) )

	#	print 'usesSet', usesSet
		#usesSet = usesSet.difference( set( ['sofa', 'cairo1-7-6', 'gtkmm2-14-3', 'itk3-4-0'] ) ) # @todo not very cute and robust to different gtkmm version.
		usesSet = usesSet.difference( set( ['cairo1-7-6', 'gtkmm2-14-3', 'itk3-4-0'] ) ) # @todo not very cute and robust to different gtkmm version.
	#	print 'usesSet filtered', usesSet
	#	print

		usesFromDependencies = usesSet.difference( usesAlreadyConfigured )
	#	print 'usesSet', usesSet.difference( usesAlreadyConfigured )
	#	print 'usesFromDependencies', usesFromDependencies
		uses( self, lenv, list(usesFromDependencies), True ) #list(usesFromDependencies) )#, True ) # True for skipLinkStageConfiguration
		#['boost1-38-0']
#		print

		###### setup 'pseudo BuildDir' (with OBJPREFIX) ######									###todo use builddir ?
		### TODO: .cpp .cxx .c => config.options global, idem for pruneDirectories, .h .... => config.options global ?
		filesFromSrc		= []
		filesFromInclude	= []
		filesFromShare		= []

		basenameWithDotRe = r"^[a-zA-Z][a-zA-Z0-9_\-]*\."

		searchFiles( 'src',		filesFromSrc,		['.svn'], basenameWithDotRe + r"cpp$" )
		#searchFiles1( 'src',		['.svn'], ['.cpp'], filesFromSrc )

		searchFiles( 'include',	filesFromInclude,	['.svn'], basenameWithDotRe + r"(?:hpp|hxx|h|inl)$" )
		#searchFiles1( 'include', ['.svn'], ['.hpp','.hxx','.h'], filesFromInclude )

		searchFiles( 'share',	filesFromShare,		['.svn'] )

		objFiles = []
		if		self.myType in ['exec', 'static'] :
			for srcFile in filesFromSrc :
				objFile			=	(os.path.splitext(srcFile)[0]).replace('src', self.myProjectBuildPathExpanded, 1 )
				srcFileExpanded	=	os.path.join(self.myProjectPathName, srcFile)
				objFiles		+=	lenv.Object( objFile, srcFileExpanded )				# Object is a synonym for the StaticObject builder method.
				### print objFile, ':', srcFileExpanded, '\n'

		elif	self.myType == 'shared':
			for srcFile in filesFromSrc :
				objFile			=	(os.path.splitext(srcFile)[0]).replace('src', self.myProjectBuildPathExpanded, 1 )
				srcFileExpanded	=	os.path.join(self.myProjectPathName, srcFile)
				objFiles		+=	lenv.SharedObject( objFile, srcFileExpanded )
				### print objFile, ':', srcFileExpanded, '\n'
		else :
			if	self.myType != 'none' :
				print 'sbfWarning: during setup of pseudo BuildDir'
			# else nothing to do for 'none'

		### Processes win32 resource files
		# @todo generalizes a rc system
		# @todo a lib for rc/share resource (in a zip) ?
#env.Alias( self.myProject + '_resource.rc_generation' )
		Alias( self.myProject + '_resource.rc_generation' )

		if self.myPlatform == 'win32' :
			# Uses a specialized environment for rc compiler
			rcEnv = lenv.Clone()

			# Configures CPPPATH for PSDK
			if self.myIsExpressEdition :
				rcEnv.Append( CPPPATH = 'C:\\Program Files\\Microsoft Platform SDK for Windows Server 2003 R2\\Include' )

			# Adds rc directory to CPPPATH
			rcPath = os.path.join(self.myProjectPathName, 'rc')
			if os.path.isdir( rcPath ):
				# Appends rc to CPPPATH
				rcEnv.Append( CPPPATH = rcPath )

			# Compiles resource.rc
			rcFile = os.path.join(rcPath, 'resource.rc')
			if os.path.isfile( rcFile ):
				# Compiles the resource file
				objFiles += rcEnv.RES( rcFile )
				lenv['sbf_rc'] = [rcFile]
			else:
				lenv['sbf_rc'] = []

			# Generates resource_sbf.rc file
			sbfRCFile = os.path.join(self.myProjectBuildPathExpanded, 'resource_sbf.rc')
			Alias(	self.myProject + '_resource_generation',
					rcEnv.Command( sbfRCFile, 'dummy.in', Action( resourceFileGeneration, printGenerate ) ) )
			objFiles += rcEnv.RES( sbfRCFile )

			# @todo FIXME not very cute, same code in sbfRC
			iconFile		= lenv['sbf_project'] + '.ico'
			iconAbsPathFile	= os.path.join(lenv['sbf_projectPathName'], 'rc', iconFile )
			if os.path.isfile( iconAbsPathFile ) :
				lenv['sbf_rc'].append( iconAbsPathFile )

		### final result of project ###
		objProject = os.path.join( self.myProjectBuildPathExpanded, self.myProject ) + '_' + self.myVersion + self.my_Platform_myCCVersion

		objProject += self.my_FullPostfix

		#
		installInBinTarget		= []
		installInIncludeTarget	= []
		installInLibTarget		= []
		installInShareTarget	= filesFromShare

		if		self.myType == 'exec' :
			projectTarget			=	lenv.Program( objProject, objFiles )
			installInBinTarget		+=	projectTarget
		elif	self.myType == 'static' :
			projectTarget			=	lenv.StaticLibrary( objProject, objFiles )
			installInLibTarget		+=	projectTarget
			installInIncludeTarget	+=	filesFromInclude
		elif	self.myType == 'shared' :
			projectTarget			=	lenv.SharedLibrary( objProject, objFiles )
			installInLibTarget		+=	projectTarget
			installInIncludeTarget	+=	filesFromInclude
		elif self.myType == 'none' :
			projectTarget			=	''
			installInIncludeTarget	+=	filesFromInclude
		else :
			print 'sbfWarning: during final setup of project'

#===============================================================================
#		if self.myType in ['exec', 'static', 'shared'] :
#			# projectTarget is not deleted before it is rebuilt.
#			lenv.Precious( projectTarget )
#===============================================================================

		# PDB: pdb only generate on win32 and in debug mode.
#===============================================================================
#		if (self.myPlatform == 'win32') and (self.myConfig == 'debug') :
#			# PDB Generation
#			# static library don't generate pdb.
#			if	self.myType in ['exec', 'shared'] :
#				#lenv['PDB'] = objProject + '.pdb'
#				#lenv.SideEffect( lenv['PDB'], projectTarget )
#				# it is not deleted before it is rebuilt.
#				#lenv.Precious( lenv['PDB'] )
#
#			# PDB Installation
#			if		self.myType == 'exec' :
#				installInBinTarget.append(	File(lenv['PDB'])	)
#			elif	self.myType == 'shared' :
#				installInLibTarget.append(	File(lenv['PDB'])	)
#===============================================================================


		######	setup targets : myProject_svnCheckout, myProject_svnUpdate, myProject_build myProject_install myProject myProject_clean myProject_mrproper ######

		### myProject_svnCheckout
#???
		#Alias( self.myProject + '_svnCheckout', lenv.Command('dummySvnCheckout.out1', 'dummy.in', Action( nopAction, nopAction ) ) )
#env.Alias( self.myProject + '_svnCheckout', env.Command('dummySvnCheckout.out1', 'dummy.in', Action( nopAction, nopAction ) ) )

		### myProject_svnUpdate
#???
		#Alias( self.myProject + '_svnUpdate', lenv.Command('dummySvnUpdate.out1', 'dummy.in', Action( nopAction, nopAction ) ) )
#env.Alias( self.myProject + '_svnUpdate', env.Command('dummySvnUpdate.out1', 'dummy.in', Action( nopAction, nopAction ) ) )

		### myProject_build
		Alias( self.myProject + '_build_print', lenv.Command('dummy_build_print' + self.myProject + 'out1', 'dummy.in', Action( nopAction, printEmptyLine ) ) )
		Alias( self.myProject + '_build_print', lenv.Command('dummy_build_print' + self.myProject + 'out2', 'dummy.in', Action( nopAction, printBuild ) ) )
		AlwaysBuild( self.myProject + '_build_print' )
#env.Alias( self.myProject + '_build_print', env.Command('dummy_build_print' + self.myProject + 'out1', 'dummy.in', Action( nopAction, printEmptyLine ) ) )
#env.Alias( self.myProject + '_build_print', lenv.Command('dummy_build_print' + self.myProject + 'out2', 'dummy.in', Action( nopAction, printBuild ) ) )
#env.AlwaysBuild( self.myProject + '_build_print' )

		aliasProjectBuild = Alias( self.myProject + '_build', self.myProject + '_build_print' )
		Alias( self.myProject + '_build', self.myProject + '_resource.rc_generation' )
		Alias( self.myProject + '_build', projectTarget )
		Clean( self.myProject + '_build', self.myProjectBuildPathExpanded  )
#aliasProjectBuild = env.Alias( self.myProject + '_build', self.myProject + '_build_print' )
#env.Alias( self.myProject + '_build', self.myProject + '_resource.rc_generation' )
#env.Alias( self.myProject + '_build', projectTarget )
#env.Clean( self.myProject + '_build', self.myProjectBuildPathExpanded  )

		### myProject_install
		if len(installInBinTarget) > 0 :
			MSVSProjectBuildTarget	= lenv.Install( os.path.join(self.myInstallDirectory, 'bin'), installInBinTarget )
			installTarget			= MSVSProjectBuildTarget
		else :
			MSVSProjectBuildTarget	= []
			installTarget			= []

		for file in installInIncludeTarget :
			installTarget += lenv.InstallAs( os.path.join(self.myInstallDirectory, file), os.path.join(self.myProjectPathName, file) )

		if len(installInLibTarget) > 0 :
			MSVSProjectBuildTarget = lenv.Install( os.path.join(self.myInstallDirectory, 'lib'), installInLibTarget )
			installTarget.append( MSVSProjectBuildTarget )

		for file in installInShareTarget :
			installTarget += lenv.InstallAs(	file.replace('share', self.getShareInstallDirectory(), 1),
												os.path.join(self.myProjectPathName, file) )

		#
		Alias( self.myProject + '_install_print', lenv.Command('dummy_install_print' + self.myProject + 'out1', 'dummy.in', Action( nopAction, printInstall ) ) )
		AlwaysBuild( self.myProject + '_install_print' )
#env.Alias( self.myProject + '_install_print', lenv.Command('dummy_install_print' + self.myProject + 'out1', 'dummy.in', Action( nopAction, printInstall ) ) )
#env.AlwaysBuild( self.myProject + '_install_print' )

		aliasProjectInstall = Alias( self.myProject + '_install', self.myProject + '_build' )
		Alias( self.myProject + '_install', self.myProject + '_install_print' )
		Alias( self.myProject + '_install', installTarget )
#aliasProjectInstall = env.Alias( self.myProject + '_install', self.myProject + '_build' )
#env.Alias( self.myProject + '_install', self.myProject + '_install_print' )
#env.Alias( self.myProject + '_install', installTarget )

		### myProject
		aliasProject = Alias( self.myProject, aliasProjectInstall )
#aliasProject = env.Alias( self.myProject, aliasProjectInstall )

#===============================================================================
#		### myProject_vcprojog
#		### TODO: Adds vcproj files to clean/mrproper
#		### TODO: Adds target vcsln
#		if len(MSVSProjectBuildTarget) > 0 :
#			env.Alias(	self.myProject + '_vcprojog_print',
#						lenv.Command(	'dummy_vcprojog_print' + self.myProject + 'out1', 'dummy.in',
#										Action( nopAction, printVisualStudioProjectBuild ) ) )
#
#			vcprojFile		= os.path.join( self.myProjectPathName, self.myProject + 'og' ) + env['MSVSPROJECTSUFFIX']
#			optionsFiles	= glob.glob( self.myProjectPathName + os.sep + '*.options' )
#
#			if self.myConfig == 'release' :
#				MSVSProjectVariant = ['Release']
#			else :
#				MSVSProjectVariant = ['Debug']
#
#			vcprojTarget = env.MSVSProject(
#								target		= vcprojFile,
#								srcs		= filesFromSrc,
#								incs		= filesFromInclude,
#								resources	= filesFromShare,
#								misc		= optionsFiles,
#								buildtarget = MSVSProjectBuildTarget[0],
#								variant		= MSVSProjectVariant,
#								auto_build_solution = 0 )
#
#			aliasVCProjTarget = env.Alias( self.myProject + '_vcprojog', self.myProject + '_vcprojog_print' )
#			env.Alias( self.myProject + '_vcprojog', vcprojTarget )
#			###### target vcprojog ######
#			env.Alias( 'vcprojog', aliasVCProjTarget )
#		# else no build target, so do nothing
#===============================================================================

		### myProject_clean

		### FIXME																					printClean does'nt work ??? modified behavior when clean=1 ?
		#env.Alias( self.myProject + '_clean_print', lenv.Command('dummy_clean_print' + self.myProject + 'out1', 'dummy.in', Action( nopAction, printEmptyLine ) ) )
		#env.Alias( self.myProject + '_clean_print', lenv.Command('dummy_clean_print' + self.myProject + 'out2', 'dummy.in', Action( nopAction, printClean ) ) )
		#env.AlwaysBuild( self.myProject + '_clean_print' )
		#env.Alias( self.myProject + '_clean', self.myProject + '_clean_print' )

		aliasProjectClean = Alias( self.myProject + '_clean', self.myProject + '_build' )
#aliasProjectClean = env.Alias( self.myProject + '_clean', self.myProject + '_build' )

		### myProject_mrproper
		# TODO: printMrproper see myProject_clean target.

		aliasProjectMrproper = Alias( self.myProject + '_mrproper', aliasProjectInstall )
		Clean( self.myProject + '_mrproper', os.path.join(self.myProjectBuildPath, self.myProject) )
		Clean( self.myProject + '_mrproper', os.path.join(self.myInstallDirectory, 'include', self.myProject) )
#aliasProjectMrproper = env.Alias( self.myProject + '_mrproper', aliasProjectInstall )
#env.Clean( self.myProject + '_mrproper', os.path.join(self.myProjectBuildPath, self.myProject) )
#env.Clean( self.myProject + '_mrproper', os.path.join(self.myInstallDirectory, 'include', self.myProject) )

		shareProjectInstallDirectory = os.path.join( self.myInstallDirectory, 'share', self.myProject )
		if os.path.exists( shareProjectInstallDirectory ) :
			shareProjectInstallEntries = os.listdir( shareProjectInstallDirectory )
			if	len(shareProjectInstallEntries) == 0 or \
				(len(shareProjectInstallEntries) == 1 and shareProjectInstallEntries[0] == self.myVersion) :
				Clean( self.myProject + '_mrproper', shareProjectInstallDirectory )
#env.Clean( self.myProject + '_mrproper', shareProjectInstallDirectory )
			else :
				Clean( self.myProject + '_mrproper', self.getShareInstallDirectory() )
#env.Clean( self.myProject + '_mrproper', self.getShareInstallDirectory() )
		# else : nothing to do, no share/myProject directory

		# TODO: and the local/doc/myProject directory ?

		#@todo myproject_zip

		### Configures lenv
		lenv['sbf_bin']							= []
		lenv['sbf_include']						= filesFromInclude
		lenv['sbf_share']						= filesFromShare
		lenv['sbf_src']							= filesFromSrc
		lenv['sbf_lib_object']					= []
		lenv['sbf_lib_object_for_developer']	= []
		lenv['sbf_files']						= glob.glob( self.myProjectPathName + os.sep + '*.options' )
# @todo sbf_rc, others ?

		for elt in installInBinTarget :
			lenv['sbf_bin'].append( elt.abspath )

		# @todo: not very platform independent
		for elt in installInLibTarget :
			# TODO: must be optimize
			absPathFilename	= elt.abspath
			filename		= os.path.split(absPathFilename)[1]
			filenameExt		= os.path.splitext(filename)[1]
			if filenameExt == '.exp' :
				# exclude *.exp
				continue
			if filenameExt in ['.pdb', '.lib'] :
				lenv['sbf_lib_object_for_developer'].append( absPathFilename )
			else :
				lenv['sbf_lib_object'].append( absPathFilename )

		###### special targets: build install all clean mrproper ######
		Alias( 'build',		aliasProjectBuild		)
		Alias( 'install',	aliasProjectInstall		)
		Alias( 'all',		aliasProject			)
		Alias( 'clean',		aliasProjectClean		)
		Alias( 'mrproper',	aliasProjectMrproper	)
#env.Alias( 'build',		aliasProjectBuild		)
#env.Alias( 'install',	aliasProjectInstall		)
#env.Alias( 'all',		aliasProject			)
#env.Alias( 'clean',		aliasProjectClean		)
#env.Alias( 'mrproper',	aliasProjectMrproper	)

		# a vcs add ?
		tryVcsAdd = 'svnAdd' in self.myBuildTargets

		if tryVcsAdd :
			#if lenv['vcsUse'] == 'yes' :	# @todo moves this test in vcsOperation
			self.vcsAdd( lenv )
			#else:
			#	if lenv.GetOption('verbosity') :
			#		print "Skip project %s in %s" % (self.myProject, self.myProjectPath)


	###### Helpers ######
	### share directory
	def getShareDirectory( self ) :
		return os.path.join( 'share', self.myProject, self.myVersion )

	def getShareInstallDirectory( self ) :
		return os.path.join( self.myInstallDirectory, self.getShareDirectory() )

	### Management of version number
	# @todo moves to sbfVersion.py
	def computeVersionNumber( self, versionNumberList ):
		versionNumber	= 0
		coef			= 1.0
		for version in versionNumberList :
			versionNumber += float(version) / coef
			coef = coef / 1000.0
		return versionNumber

	def getVersionNumberTuple( self, versionNumber ) :
		major				= int(versionNumber)
		minorDotMaintenance	= (versionNumber-major)*1000
		minor				= int(minorDotMaintenance)
		maintenance			= int((minorDotMaintenance-minor)*1000)
		return ( major, minor, maintenance )

	def getVersionNumberString1( self, versionNumber ) :
		return str( int(versionNumber) )

	def getVersionNumberString2( self, versionNumber ) :
		tuple = self.getVersionNumberTuple( versionNumber )
		return "%u-%u" % ( tuple[0], tuple[1] )

	def getVersionNumberString3( self, versionNumber ) :
		tuple = self.getVersionNumberTuple( versionNumber )
		return "%u-%u-%u" % ( tuple[0], tuple[1], tuple[2] )



	###
	#
	def getDepsProjectName( self, lenv, keepOnlyExistingProjects = True ):
		if keepOnlyExistingProjects :
			retVal = []
			for dep in lenv['deps']:
				projectName = os.path.basename(getNormalizedPathname(dep))
				if projectName in self.myParsedProjects :		# @todo uses a set()
					retVal.append( projectName )
				#else nothing to do
			return retVal
		else:
			retVal = []
			for dep in lenv['deps']:
				projectName = os.path.basename(getNormalizedPathname(dep))
				retVal.append( projectName )
			return retVal

	# Collects recursively all dependencies of the project with the given environment.
	# Returns a list containing project name of all its dependencies.
	def getAllDependencies( self, lenv ) :#, keepOnlyExistingProjects = True ):
		stackDependencies			= self.getDepsProjectName(lenv) #, keepOnlyExistingProjects)
		recursiveDependenciesSet	= set()
		recursiveDependencies		= []
#		for elt in stackDependencies :
#			if elt not in recursiveDependenciesSet and elt in self.myParsedProjects :
#				recursiveDependenciesSet.add( elt )
#				recursiveDependencies.append( elt )

		while ( len(stackDependencies) > 0 ):
			dependencyName	= stackDependencies.pop(0)
			if dependencyName not in recursiveDependenciesSet:
				recursiveDependenciesSet.add( dependencyName )
				recursiveDependencies.append( dependencyName )
			else:
				continue

			dependencyEnv	= self.myParsedProjects[ dependencyName ]
			stackDependencies += self.getDepsProjectName( dependencyEnv )

#			for elt in depsProjectName :
#				if elt not in recursiveDependenciesSet and elt in self.myParsedProjects :
#					recursiveDependenciesSet.add( elt )
#					recursiveDependencies.append( elt )
#					stackDependencies.append( elt )
		return recursiveDependencies
