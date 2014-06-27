# SConsBuildFramework - Copyright (C) 2009, 2012, 2013, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import os
import re

from src.sbfFiles import getNormalizedPathname

# To be able to use sbfVersion.py without SCons
import __builtin__
try:
	from SCons.Script import *
except ImportError as e:
	if not hasattr(__builtin__, 'SConsBuildFrameworkQuietImport'):
		print ('sbfWarning: unable to import SCons.Script')


### Helpers to retrieve/print version of SConsBuildFramework ###
def printSBFVersion():
	print ( 'SConsBuildFramework version : {0}'.format(getSBFVersion()) )


def getSBFVersion():
	# Retrieves and normalizes SCONS_BUILD_FRAMEWORK
	sbfRoot = getNormalizedPathname( os.getenv('SCONS_BUILD_FRAMEWORK') )

	# Reads version number in VERSION file
	versionFile	= os.path.join(sbfRoot, 'VERSION')
	if os.path.lexists( versionFile ) :
		with open( versionFile ) as file :
			return file.readline()
	else :
		return "Missing {0} file. So version number is unknown.".format(versionFile)



### Helpers to manage version (number and string)
def computeVersionNumber( versionNumberList ):
	versionNumber	= 0
	coef			= 1.0
	for version in versionNumberList :
		versionNumber += float(version) / coef
		coef = coef * 1000.0
	return versionNumber

def getVersionNumberTuple( versionNumber ) :
	major				= int(versionNumber)
	minorDotMaintenance	= (versionNumber-major)*1000
	minor				= int( round(minorDotMaintenance) )
	maintenance			= int( round((minorDotMaintenance-minor)*1000) )
	return ( major, minor, maintenance )

def getVersionNumberString1( versionNumber ) :
	return str( int(versionNumber) )

def getVersionNumberString2( versionNumber ) :
	tuple = getVersionNumberTuple( versionNumber )
	return "%u-%u" % ( tuple[0], tuple[1] )

def getVersionNumberString3( versionNumber ) :
	tuple = getVersionNumberTuple( versionNumber )
	return "%u-%u-%u" % ( tuple[0], tuple[1], tuple[2] )



### Helpers to extract version ###
versionPattern = '(?P<version>(?:(?P<major>[0-9]+)(?:-(?P<minor>[0-9]+))?(?:-(?P<maint>[0-9]+))?(?:-(?P<postfix>[a-zA-Z0-9]+))?)?)'
versionRE = re.compile( r'^{0}$'.format(versionPattern) )

versionDoc = "The project version must follow the schema no version at all or major-[postfix] or major-minor-[postfix] or major-minor-maintenance[-postfix].\nmajor, minor, maintenance and postfix can contain any decimal digit. In addition, postfix can contain any alphabetical character."

def extractVersion( versionStr ):
	""" Returns a tuple containing (major, minor, maintenance, postfix) version information from versionStr (major[-minor][-maintenance][-postfix]).
		See versionDoc"""
	versionMatch = versionRE.match( versionStr )
	if versionMatch:
		return (versionMatch.group('major'), versionMatch.group('minor'), versionMatch.group('maint'), versionMatch.group('postfix'))
	else:
		raise SCons.Errors.UserError("Given version:{0}.\n{1}".format(versionStr, versionDoc) )

### Helpers to split 'uses' or 'libs' value ###
#'uses' 'libs'
#name azerty
#	 AzErTy
#	 azer2ty
#	 azer_tY
#	 glc_gtkmm
#	 python-runtime
#version see extractVersion()
usesNamePattern = '(?P<name>[a-zA-Z]+(?:[\d_][a-zA-Z]+|)(|\-runtime|\-runtime-release|\-runtime-debug))'
usesORlibsSplitter = re.compile( r'^{0}[ \t]*{1}$'.format(usesNamePattern, versionPattern) )
nameDoc = ''

def splitUsesORlibs( value, text ):
	"""@return (name, version) from 'nameVersion', 'name' or 'name version'.
	@remark Example: splitUsesORlibs( 'boost1-48-0' ) returns ('boost', '1-48-0')
	See versionDoc"""

	match = usesORlibsSplitter.match( value )
	if match:
		return (match.group('name'), match.group('version'))
	else:
		raise SCons.Errors.UserError("{0}=['{1}'].\n The following schemas must be used ['nameVersion'], ['name'] or ['name version'].\n{2}".format(text, value, versionDoc) )

def splitUsesName( singleUsesValue ):
	"""See splitUsesORlibs()"""

	return splitUsesORlibs( singleUsesValue, 'uses' )

def splitLibsName( singleLibsValue ):
	"""See splitUsesORlibs()"""

	return splitUsesORlibs( singleLibsValue, 'libs' )

#print splitUsesName('opengl')
#print splitUsesName('boost1-48-0')
#print splitUsesName('usb2brd1-0')

### Helpers to split package name ###
packagePlatform = '(?P<platform>.+)'
packageArch = '(?P<arch>.+)'
packageCC = '(?P<cc>.+)'
packageExtension = '(?P<extension>.+)'

def splitPackageName( packageName ):
	"""@remark Example: splitPackageName( 'opencollada865_win_x86-64_cl10-0Exp.zip' ) returns 
	{	'name'		: 'opencollada',
		'version'	: '865',
		'platform'	: 'win',
		'arch'		: 'x86-64',
		'cc'		: 'cl10-0Exp',
		'extension'	: 'zip' }"""
	splitter = re.compile( r'^{0}{1}_{2}_{3}_{4}[.]{5}$'.format( usesNamePattern, versionPattern, packagePlatform, packageArch, packageCC, packageExtension ) )
	match = splitter.match( packageName )
	if match:
		return {	'name'		: match.group('name'),
					'version'	: match.group('version'),
					'platform'	: match.group('platform'),
					'arch'		: match.group('arch'),
					'cc'		: match.group('cc'),
					'extension'	: match.group('extension') }
	else:
		print ("Unable to split package name {0}. The following schemas must be used 'nameVersion_platform_arch_ccVersion.extension'.".format(packageName) )
		return

def joinPackageName( pakInfo ):
	"""@remark Example: tmp = {
		'name'		: 'opencollada',
		'version'	: '865',
		'platform'	: 'win',
		'arch'		: 'x86-64',
		'cc'		: 'cl10-0Exp',
		'extension'	: 'zip' }
		joinPackageName(tmp) returns 'opencollada865_win32_cl10-0Exp.zip'
	"""
	return "{0}{1}_{2}_{3}_{4}.{5}".format( pakInfo['name'], pakInfo['version'], pakInfo['platform'], pakInfo['arch'], pakInfo['cc'], pakInfo['extension'] )


### Helpers to split 'deploymentPrecond' ###
operatorPattern = '(?P<operator>==|>=|>|<|<=)'
deploymentPrecondSplitter = re.compile( r'^{0}[ \t]+{1}[ \t]+{2}$'.format( usesNamePattern, operatorPattern, versionPattern ) )
operatorDoc = 'versionOperator have to be choosen among ==, >=, >, < and <=.'

def splitDeploymentPrecond( deploymentPrecond ):
	"""	Split and verify the deploymentPrecond option of sbf project
		@param deploymentPrecond		allowed schemas 'projectName versionOperator version'.
		versionOperator have to be choosen among ==, >=, >, < and <=. version have to follow the classical sbf version convention.
		@return (projectName, versionOperator, version) or None if deploymentPrecond is not valid."""
	match = deploymentPrecondSplitter.match( deploymentPrecond )
	if match:
		return (match.group('name'), match.group('operator'), match.group('version'))
	else:
		raise SCons.Errors.UserError("deploymentPrecond='{0}'.\n The following schema have to be used 'projectName versionOperator version'.\n{1}\n{2}\n{3}".format(deploymentPrecond, nameDoc, operatorDoc, versionDoc) )
