#!/usr/bin/env python
# SConsBuildFramework - Copyright (C) 2012, 2013, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier


from optparse import OptionParser
from os.path import join
import os, sys


# @todo import argparse
# @todo publishPath = '../../publish' and publishOn	= True ?
# @todo --srcPak => --svnExport and scons svnExport
# @todo --project name --branch tags/0.1


# Command line options
usage = """Usage: sbfInit.py [Options]"""
parser = OptionParser(usage)
parser.add_option(	"-s", "--switch", action="store_true", dest="switch", default=False,
					help="Switch from one SConsBuildFramework installation to another one (i.e. update the current SConsBuildFramework configuration to use the SConsBuildFramework found in the current directory)." )
parser.add_option(	"-v", "--verbose", action="store_true", dest="verbose", default=False,
					help="increase verbosity" )
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
# @todo sbf = SConsBuildFramework()
sbf = SConsBuildFramework( initializeOptions = False )

# Import several functionalities from sbf
import __builtin__
__builtin__.SConsBuildFrameworkQuietImport = True

from src.sbfAllVcs import *
from src.sbfConfiguration import sbfConfigure, sbfUnconfigure
from src.sbfEnvironment import Environment
from src.sbfPaths import Paths
from src.sbfSubversion import locateProject, remoteListSbfTags, remoteListSbfBranches, remoteGetTagContents, remoteGetBranchesContents, anonymizeUrl, removeTrunkOrTagsOrBranches
from src.sbfUtils import getDictPythonCode, printSeparator
from src.sbfUI import *
from src.SConsBuildFramework import getSConsBuildFrameworkOptionsFileLocation

# Helpers
import multiprocessing

def createNewSConsBuildFramework( vcs, newSbfRoot, trunkAndHeadRevision = False ):
	"""Checkout SConsBuildFramework in newSbfRoot directory"""
	(sbfSvnUrl, sbfRevision) = vcs.locateProject( 'SConsBuildFramework' )
	if not sbfSvnUrl:
		print ( "SConsBuildFramework not found. Check your 'svnUrls' SConsBuildFramework option." )
		exit(1)
	else:
		if trunkAndHeadRevision:
			sbfSvnUrl = removeTrunkOrTagsOrBranches(sbfSvnUrl)+'/trunk'
			sbfRevision = None
		vcs._checkout( sbfSvnUrl, newSbfRoot, sbfRevision )


def fullyConfigureSConsBuildFramework( sbf, oldSbfRoot, sbfRoot, oldConfiguration, newConfiguration, verbose ):
	assert( 'svnUrls' in newConfiguration )
	assert( 'installPath' in newConfiguration )
	assert( 'buildPath' in newConfiguration )

	# old configuration
	unconfigureSConsBuildFramework( sbf, verbose )

	# new configuration
	setSCONS_BUILD_FRAMEWORK( sbfRoot, verbose )
	createSConsBuildFrameworkOptionsFile( sbfRoot, oldConfiguration, newConfiguration, verbose)
	sbf = configureSConsBuildFramework( sbfRoot, verbose )
	return sbf


def unconfigureSConsBuildFramework( sbf, verbose ):
	# Unconfiguring current SConsBuildFramework
	print ('* Unconfiguring current SConsBuildFramework')
	sbfUnconfigure(sbf, takeCareOfSofa=False, takeCareOfSBFRuntimePaths = True, verbose = verbose)
	print


def setSCONS_BUILD_FRAMEWORK( newSCONS_BUILD_FRAMEWORK, verbose ):
	# Updating SCONS_BUILD_FRAMEWORK
	environment = Environment()
	print ('* Updating SCONS_BUILD_FRAMEWORK')
	environment.set( 'SCONS_BUILD_FRAMEWORK', newSCONS_BUILD_FRAMEWORK, verbose )
	print


# numJobs from newConfiguration, otherwise multiprocessing.cpu_count()
# outputLineLength from newConfiguration, otherwise do nothing
# pakPaths from newConfiguration if available, otherwise oldConfiguration, otherwise []
# svnUrls from newConfiguration
# projectExclude, weakLocalExtExclude svnCheckoutExclude, svnUpdateExclude
# clVersion from newConfiguration if available, otherwise oldConfiguration, otherwise highest
# installPath and buildPath from newConfiguration
# config from newConfiguration, otherwise do nothing
# generateDebugInfoInRelease from newConfiguration, otherwise do nothing
def createSConsBuildFrameworkOptionsFile( sbfRoot, oldConfiguration, newConfiguration, verbose):
	# Configuration file of the newly created SConsBuildFramework
	print ('* Creating the SConsBuildFramework.options file')
	with open( join(sbfRoot, 'SConsBuildFramework.options'), 'w' ) as newConfigFile:
		numJobs = newConfiguration.get( 'numJobs', multiprocessing.cpu_count() )
		newConfigFile.write( 'numJobs					= {0}\n'.format(numJobs) )

		if 'outputLineLength' in newConfiguration:
			newConfigFile.write( 'outputLineLength		= {0}\n'.format(newConfiguration['outputLineLength']) )

		pakPaths = newConfiguration.get('pakPaths', oldConfiguration.get('pakPaths', []))
		newConfigFile.write( 'pakPaths				= {0}\n'.format(pakPaths) )

		newConfigFile.write('\n')
		for line in getDictPythonCode(newConfiguration['svnUrls'], 'svnUrls', orderedDict = True, eol=True):
			newConfigFile.write( line )
		newConfigFile.write('\n')

		newConfigFile.write( 'projectExclude		= []\n' )
		newConfigFile.write( "weakLocalExtExclude	= ['sofa']\n" )

		newConfigFile.write( 'svnCheckoutExclude	= []\n' )
		newConfigFile.write( 'svnUpdateExclude	= []\n' )

		clVersion = newConfiguration.get('clVersion', oldConfiguration.get('clVersion', 'highest'))
		newConfigFile.write( "clVersion			= '{0}'\n".format(clVersion) )

		newConfigFile.write( "installPath			= '{0}'\n".format(newConfiguration['installPath'].replace('\\', '\\\\')) )
		newConfigFile.write( "buildPath			= '{0}'\n".format(newConfiguration['buildPath'].replace('\\', '\\\\')) )

		if 'config' in newConfiguration:
			newConfigFile.write( 'config			= {0}\n'.format(newConfiguration['config']) )

		if 'generateDebugInfoInRelease' in newConfiguration:
			newConfigFile.write( 'generateDebugInfoInRelease		= {0}\n'.format(newConfiguration['generateDebugInfoInRelease']) )

		newConfigFile.write('\n')
		if 'usesAlias' in newConfiguration:
			for line in getDictPythonCode(newConfiguration['usesAlias'], 'usesAlias', orderedDict = True, eol=True, addImport=False):
				newConfigFile.write( '#' + line )
	print


def configureSConsBuildFramework( SCONS_BUILD_FRAMEWORK, verbose ):
	# Configuring new SConsBuildFramework
	print ('* Configuring new SConsBuildFramework')
	#	Changing SCONS_BUILD_FRAMEWORK environment variable for the current process
	os.environ['SCONS_BUILD_FRAMEWORK'] = SCONS_BUILD_FRAMEWORK

	# Creating a new sbf using the newly SConsBuildFramework and its new configuration file
	sbf = SConsBuildFramework( initializeOptions = False )

	#
	sbfConfigure(sbf, takeCareOfSofa=False, verbose=verbose)

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

#
def createNewSvnUrls( sbfConfigurationDict, branch ):
	# Constructs a new 'svnUrls' with '/{branch}'
	newSvnUrls = {}
	for (project, urls) in sbfConfigurationDict['svnUrls'].iteritems():
		if isinstance(urls, list):
			urls = [ anonymizeUrl(removeTrunkOrTagsOrBranches(url)) + '/' + branch for url in urls ]
		else:
			urls = anonymizeUrl(removeTrunkOrTagsOrBranches(urls)) + '/' + branch
		newSvnUrls[project] = urls
	return newSvnUrls


def main( options, args, sbf, vcs ):
	# Asks project name ?
	projectName = ask( 'Gives the name of the project to checkout', 'projectName' )
	projectSvnUrl = locateProject( vcs, projectName, verbose )
	# Asks which branch ?
	print
	#branch = askQuestion( "Checkout project '{0}' from trunk, tags or branches".format(projectName), ['(tr)unk', '(t)ags', '(b)ranches'] )
	branch = askQuestion( "Checkout project '{0}' from trunk or branches".format(projectName), ['(tr)unk', '(b)ranches'] )
	print

	# @todo choose destination directory (binDirectory and localDirectory)
	binDirectory = join( os.getcwd(), 'bin' )
	localDirectory = '$SCONS_BUILD_FRAMEWORK/../../local'	# <=> join( os.getcwd(), 'local' )
	buildPath = '$SCONS_BUILD_FRAMEWORK/../../build'		# <=> join( os.getcwd(), 'build' )

	projectPathName = join( binDirectory, projectName )
	sbfProjectPathName = join(binDirectory, 'SConsBuildFramework')

	newSvnUrls = None
	tagContents = ''

	if branch == 'trunk':
		# trunk chosen
		# needed to choose head or a tag file
		tagsList = remoteListSbfTags(projectSvnUrl, branch, True)

		if len(tagsList)==0:
			# no tags, so head chosen
			newSvnUrls = createNewSvnUrls(sbfConfigurationDict, branch)
		else:
			tagsList.insert(0, 'head')
			desiredTag = askQuestion( "Choose head revision or a tag among the following", tagsList )
			print
			if desiredTag == 'head':
				newSvnUrls = createNewSvnUrls(sbfConfigurationDict, branch)
			else:
				tagContents = remoteGetTagContents( projectSvnUrl, branch, desiredTag )
				if len(tagContents)==0:
					print ( 'Empty or unable to read file {}.tags'.format(desiredTag) )
					exit(1)
	else:
		# branches chosen

		# collect *.branches from trunk/branching
		branchesList = remoteListSbfBranches(projectSvnUrl, 'trunk')
		if len(branchesList)==0:
			print ('No branches available.')
			exit(1)
		desiredBranch = askQuestion( "Choose one branch among the following", branchesList )
		print

		# collect branches/desiredBranch/branching/*.tags
		tagsList = remoteListSbfTags(projectSvnUrl, 'branches/' + desiredBranch)

		if len(tagsList)==0:
			# no tags, so trunk/branching/desiredBranch.branches chosen
			tagContents = remoteGetBranchesContents( projectSvnUrl, 'trunk', desiredBranch )
			if len(tagContents)==0:
				print ( 'Empty or unable to read file {}.branches'.format(desiredBranch) )
				exit(1)
		else:
			tagsList.insert(0, 'head')
			desiredTag = askQuestion( "Choose head revision or a tag among the following", tagsList )
			print
			if desiredTag == 'head':
				# so trunk/branching/desiredBranch.branches chosen
				tagContents = remoteGetBranchesContents( projectSvnUrl, 'trunk', desiredBranch )
				if len(tagContents)==0:
					print ( 'Empty or unable to read file {}.branches'.format(desiredBranch) )
					exit(1)
			else:
				# so branches/desiredBranch/branching/desiredTag.tags
				tagContents = remoteGetTagContents( projectSvnUrl, 'branches/' + desiredBranch, desiredTag )
				if len(tagContents)==0:
					print ( 'Empty or unable to read file {}.tags'.format(desiredTag) )
					exit(1)

	if newSvnUrls == None:
		# Retrieves new configuration (at least 'svnUrls')
		newSbfConfigFileDict = {}
		exec( tagContents, globals(), newSbfConfigFileDict )
		newSvnUrls = newSbfConfigFileDict['svnUrls']

	# Updates vcs for newSvnUrls
	vcs = Subversion( svnUrls=newSvnUrls )

	# Checkout and configure sbf
	printSeparator( 'Checkout SConsBuildFramework' )
	createNewSConsBuildFramework( vcs, sbfProjectPathName )
	print

	printSeparator( 'Configuring SConsBuildFramework' )
	newSbfConfigFileDict = {	'svnUrls'		: newSvnUrls,
								'installPath'	: localDirectory,
								'buildPath'		: buildPath }
	if 'outputLineLength' in sbfConfigurationDict:				newSbfConfigFileDict['outputLineLength'] = sbfConfigurationDict['outputLineLength']
	if 'config' in sbfConfigurationDict:						newSbfConfigFileDict['config'] = sbfConfigurationDict['config']
	if 'generateDebugInfoInRelease' in sbfConfigurationDict:	newSbfConfigFileDict['generateDebugInfoInRelease'] = sbfConfigurationDict['generateDebugInfoInRelease']
	sbf = fullyConfigureSConsBuildFramework( sbf, sbf_root, sbfProjectPathName, sbfConfigurationDict, newSbfConfigFileDict, options.verbose )
	print

	# Checkout the root project
	printSeparator( 'Checkout {0}'.format(projectName) )
	(projectSvnUrl, projectRevision ) = vcs.locateProject( projectName )
	vcs._checkout( projectSvnUrl, projectPathName, projectRevision )
	print

	printSeparator('What remains to be done')
	print ('Restart your command prompt to take care of the new SConsBuildFramework (SCONS_BUILD_FRAMEWORK and PATH environment variables).')
	print ('cd $SCONS_BUILD_FRAMEWORK; cd ../{0}'.format(projectName))
	print ('scons svnCheckout;scons pakUpdate;scons debug;scons release')


def commandSwitch( options, args, sbf, vcs ):
	newSbfRoot = os.getcwd()

	# check if cwd is an SConsBuildFramework installation
	if not os.path.exists('SConsBuildFramework.options'):
		print ('{0} seems to be an invalid SConsBuildFramework installation directory.'.format(newSbfRoot))
		exit(1)
	# old configuration
	unconfigureSConsBuildFramework( sbf, verbose )

	# new configuration

	setSCONS_BUILD_FRAMEWORK( newSbfRoot, verbose )
	sbf = configureSConsBuildFramework( newSbfRoot, verbose )

	#
	printSeparator('What remains to be done')
	print ('Restart your command prompt to take care of the modifications')

if __name__ == "__main__":
	if options.switch:
		commandSwitch( options, args, sbf, vcs )
	else:
		exitCode = main( options, args, sbf, vcs )
		sys.exit(exitCode)
#else nothing to do

