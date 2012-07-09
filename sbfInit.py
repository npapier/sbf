#!/usr/bin/env python
# SConsBuildFramework - Copyright (C) 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from optparse import OptionParser
from os.path import join
import os, sys

# Command line options
usage = """Usage: sbfInit.py [Options]"""
parser = OptionParser(usage)
parser.add_option(	"-v", "--verbose", action="store_true", dest="verbose", default=False,
					help="increase verbosity")
(options, args) = parser.parse_args()
verbose = options.verbose

# Locate sbf and add it to sys.path
sbf_root = os.getenv('SCONS_BUILD_FRAMEWORK')
if not sbf_root:
	raise StandardError("SCONS_BUILD_FRAMEWORK is not defined")
sbf_root_normalized	= os.path.normpath( os.path.expandvars( sbf_root ) )
sys.path.append( sbf_root_normalized )

# Step needed to be able to create an SConsBuildFramework instance
from src.sbfTools import locateProgram
pythonLocation = locateProgram('python')
sys.path.append( join(pythonLocation, 'Scripts') )	# to import scons in the next line
from scons import *									# to add 'C:\\Python27\\Lib\\site-packages\\scons-2.1.0' in sys.path

from src.SConsBuildFramework import *
sbf = SConsBuildFramework( initializeOptions = False )

# Import several functionalities from sbf
import __builtin__
__builtin__.SConsBuildFrameworkQuietImport = True

from src.sbfAllVcs import *
from src.sbfConfiguration import sbfConfigure, sbfUnconfigure
from src.sbfEnvironment import Environment
from src.sbfPaths import Paths
from src.sbfSubversion import SvnCat, branches2branch, listSbfBranch, splitSvnUrl, anonymizeUrl, removeTrunkOrTagsOrBranches
from src.sbfUtils import getDictPythonCode, printSeparator
from src.sbfUI import *
from src.SConsBuildFramework import getSConsBuildFrameworkOptionsFileLocation

# Helpers
import multiprocessing

def createNewSConsBuildFramework( vcs, newSbfRoot, trunkAndHeadRevision = False ):
	(sbfSvnUrl, sbfRevision) = vcs.locateProject( 'SConsBuildFramework' )
	if not sbfSvnUrl:
		print ( "SConsBuildFramework not found. Check your 'svnUrls' SConsBuildFramework option." )
		exit(1)
	else:
		if trunkAndHeadRevision:
			sbfSvnUrl = removeTrunkOrTagsOrBranches(sbfSvnUrl)+'/trunk'
			sbfRevision = None
		vcs._checkout( sbfSvnUrl, newSbfRoot, sbfRevision )


# numJobs from newConfiguration, otherwise multiprocessing.cpu_count()
# outputLineLength from newConfiguration, otherwise do nothing
# pakPaths from newConfiguration if available, otherwise oldConfiguration, otherwise []
# svnUrls from newConfiguration
# projectExclude, weakLocalExtExclude svnCheckoutExclude, svnUpdateExclude
# clVersion from newConfiguration if available, otherwise oldConfiguration, otherwise highest
# installPaths and buildPath from newConfiguration
# config from newConfiguration, otherwise do nothing
# generateDebugInfoInRelease from newConfiguration, otherwise do nothing
def configureSConsBuildFramework( sbf, oldSbfRoot, sbfRoot, oldConfiguration, newConfiguration, verbose ):
	assert( 'svnUrls' in newConfiguration )
	assert( 'installPaths' in newConfiguration )
	assert( 'buildPath' in newConfiguration )

	environment = Environment()

	# Updating SCONS_BUILD_FRAMEWORK
	print ('* Updating SCONS_BUILD_FRAMEWORK')
	environment.set( 'SCONS_BUILD_FRAMEWORK', sbfRoot, verbose )
	print

	# Unconfiguring old SConsBuildFramework
	print ('* Unconfiguring old SConsBuildFramework')
	sbfUnconfigure(sbf, takeCareOfSBFRuntimePaths = True, verbose = verbose)
	print

	# Configuration file of the newly created SConsBuildFramework
	print ('* Creating the SConsBuildFramework.options file')
	with open( join(sbfRoot, 'SConsBuildFramework.options'), 'w' ) as newConfigFile:
		numJobs = newConfiguration.get( 'numJobs', multiprocessing.cpu_count() )
		newConfigFile.write( 'numJobs					= {0}\n'.format(numJobs) )

		if 'outputLineLength' in newConfiguration:
			newConfigFile.write( 'outputLineLength		= {0}\n'.format(newConfiguration['outputLineLength']) )

		pakPaths = newConfiguration.get('pakPaths', oldConfiguration.get('pakPaths', []))
		newConfigFile.write( 'pakPaths				= {0}\n'.format(pakPaths) )

		for line in getDictPythonCode(newConfiguration['svnUrls'], 'svnUrls', orderedDict = True, eol=True):
			newConfigFile.write( line )

		newConfigFile.write( 'projectExclude		= []\n' )
		newConfigFile.write( "weakLocalExtExclude	= ['sofa']\n" )

		newConfigFile.write( 'svnCheckoutExclude	= []\n' )
		newConfigFile.write( 'svnUpdateExclude	= []\n' )

		clVersion = newConfiguration.get('clVersion', oldConfiguration.get('clVersion', 'highest'))
		newConfigFile.write( "clVersion			= '{0}'\n".format(clVersion) )

		newConfigFile.write( "installPaths		= ['{0}']\n".format(newConfiguration['installPaths'].replace('\\', '\\\\')) )
		newConfigFile.write( "buildPath			= '{0}'\n".format(newConfiguration['buildPath'].replace('\\', '\\\\')) )

		if 'config' in newConfiguration:
			newConfigFile.write( 'config			= {0}\n'.format(newConfiguration['config']) )

		if 'generateDebugInfoInRelease' in newConfiguration:
			newConfigFile.write( 'generateDebugInfoInRelease		= {0}\n'.format(newConfiguration['generateDebugInfoInRelease']) )
	print

	# Configuring new SConsBuildFramework
	print ('* Configuring new SConsBuildFramework')
	#	Changing SCONS_BUILD_FRAMEWORK environment variable for the current process
	os.environ['SCONS_BUILD_FRAMEWORK'] = sbfRoot

	# Creating a new sbf using the newly SConsBuildFramework and its new configuration file
	sbf = SConsBuildFramework( initializeOptions = False )

	#
	sbfConfigure(sbf, verbose=verbose)

	return sbf

# SCONS_BUILD_FRAMEWORK current configuration
sbfConfigurationPath = getSConsBuildFrameworkOptionsFileLocation( sbf_root )
sbfConfigurationDict = {}
execfile( sbfConfigurationPath, globals(), sbfConfigurationDict )

# Version control system

# svn available ?
if not isSubversionAvailable:
	print ("Subversion is not available. Check your SConsBuildFramework installation and configuration.")
	exit(1)

# Checks validity of 'svnUrls' option.
if len(sbfConfigurationDict.get('svnUrls', '')) == 0:
	print ("Unable to do any svn checkout, because option 'svnUrls' is empty.")
	exit(1)

vcs = Subversion( svnUrls=sbfConfigurationDict['svnUrls'] )

def main( options, args, sbf, vcs ):
	# Asks project name ?
	projectName = ask( 'Gives the name of the project to checkout', 'ulis' ) # @todo ulis => projectName
	(projectSvnUrl, tmp) = vcs.locateProject( projectName, verbose )
	if not projectSvnUrl:
		print ( "{project} not found. Check your 'svnUrls' SConsBuildFramework option.".format( project=projectName ) )
		exit(1)
	else:
		# Removes /trunk or /tags or /branches of projectSvnUrl
		projectSvnUrl = removeTrunkOrTagsOrBranches(projectSvnUrl)
		print ( "{project} found at {url}".format( project=projectName, url=projectSvnUrl ) )

	# Asks which branch ?
	print
	branch = askQuestion( "Checkout project '{0}' from trunk, tags or branches".format(projectName), ['(tr)unk', '(t)ags', '(b)ranches'] )
	print

	binDirectory = join( os.getcwd(), 'bin' )
	localDirectory = join( os.getcwd(), 'local' )
	buildPath = join( os.getcwd(), 'build' )

	projectPathName = join( binDirectory, projectName )
	sbfProjectPathName = join(binDirectory, 'SConsBuildFramework')

	if branch == 'trunk':
		# Constructs a new 'svnUrls' with '/trunk'
		newSvnUrls = {}
		for (project, urls) in sbfConfigurationDict['svnUrls'].iteritems():
			if isinstance(urls, list):
				urls = [ anonymizeUrl(removeTrunkOrTagsOrBranches(url)) + '/trunk'	for url in urls ]
			else:
				urls = anonymizeUrl(removeTrunkOrTagsOrBranches(urls)) + '/trunk'
			newSvnUrls[project] = urls

		# Updates vcs for newSvnUrls
		vcs = Subversion( svnUrls=newSvnUrls )

		# Checkout and configure sbf
		printSeparator( 'Checkout SConsBuildFramework' )
		createNewSConsBuildFramework( vcs, sbfProjectPathName )
		print

		printSeparator( 'Configuring SConsBuildFramework' )
		newSbfConfigFileDict = {	'svnUrls'		: newSvnUrls,
									'installPaths'	: localDirectory,
									'buildPath'		: buildPath }
		if 'outputLineLength' in sbfConfigurationDict:				newSbfConfigFileDict['outputLineLength'] = sbfConfigurationDict['outputLineLength']
		if 'config' in sbfConfigurationDict:						newSbfConfigFileDict['config'] = sbfConfigurationDict['config']
		if 'generateDebugInfoInRelease' in sbfConfigurationDict:	newSbfConfigFileDict['generateDebugInfoInRelease'] = sbfConfigurationDict['generateDebugInfoInRelease']
		sbf = configureSConsBuildFramework( sbf, sbf_root, sbfProjectPathName, sbfConfigurationDict, newSbfConfigFileDict, options.verbose )
		print

		# Checkout the root project
		printSeparator( 'Checkout {0}'.format(projectPathName) )
		vcs._checkout( '{0}/trunk'.format(projectSvnUrl), projectPathName )
		print
	else:
		# tags or branches
		branchChoicesList = listSbfBranch(projectSvnUrl+'/trunk', branch)
		if len(branchChoicesList)==0:
			print ('No {0} available.'.format(branches2branch(branch)))
			exit(1)

		branchChoicesListWithoutExtension = [ os.path.splitext(elt)[0] for elt in branchChoicesList ]

		# Chooses one branch
		desiredBranch = askQuestion( "Choose one {branch} among the following ".format(branch=branch), branchChoicesListWithoutExtension )
		desiredBranch += '.{0}'.format( branch )
		print

		# Retrieves informations about the desired branch
		branchConfiguration = SvnCat()( projectSvnUrl + '/trunk/' + desiredBranch )

		# Retrieves new configuration (at least 'svnUrls')
		newSbfConfigFileDict = {}
		exec( branchConfiguration, globals(), newSbfConfigFileDict )

		# Updates vcs for new svnUrls
		vcs = Subversion( svnUrls=newSbfConfigFileDict['svnUrls'] )

		# Checkout and configure sbf
		printSeparator( 'Checkout SConsBuildFramework' )
		createNewSConsBuildFramework( vcs, sbfProjectPathName )
		print

		printSeparator( 'Configuring SConsBuildFramework' )
		newSbfConfigFileDict['installPaths']	= localDirectory
		newSbfConfigFileDict['buildPath']		= buildPath
		if 'outputLineLength' in sbfConfigurationDict:				newSbfConfigFileDict['outputLineLength'] = sbfConfigurationDict['outputLineLength']
		if 'config' in sbfConfigurationDict:						newSbfConfigFileDict['config'] = sbfConfigurationDict['config']
		if 'generateDebugInfoInRelease' in sbfConfigurationDict:	newSbfConfigFileDict['generateDebugInfoInRelease'] = sbfConfigurationDict['generateDebugInfoInRelease']

		sbf = configureSConsBuildFramework( sbf, sbf_root, sbfProjectPathName, sbfConfigurationDict, newSbfConfigFileDict, options.verbose )
		print

		# Checkout the root project
		printSeparator( 'Checkout {0}'.format(projectPathName) )
		(projectSvnUrl, projectRevision ) = vcs.locateProject( projectName )
		vcs._checkout( projectSvnUrl, projectPathName, projectRevision )
		print

	printSeparator('What remains to be done')
	print ('Restart your command prompt to take care of the new SConsBuildFramework (SCONS_BUILD_FRAMEWORK and PATH environment variables).')
	print ('cd $SCONS_BUILD_FRAMEWORK; cd ../{0}'.format(projectName))
	print ('scons svnCheckout;scons pakUpdate;scons debug;scons release')

if __name__ == "__main__":
	exitCode = main( options, args, sbf, vcs )
	sys.exit(exitCode)
#else nothing to do

