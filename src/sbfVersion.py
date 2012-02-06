# SConsBuildFramework - Copyright (C) 2009, 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import os
import re

from src.sbfFiles import getNormalizedPathname



### Helpers to retrieve/print version of SConsBuildFramework ###
def printSBFVersion() :
	print ( 'SConsBuildFramework version : {0}'.format(getSBFVersion()) )


def getSBFVersion() :
	# Retrieves and normalizes SCONS_BUILD_FRAMEWORK
	sbfRoot = getNormalizedPathname( os.getenv('SCONS_BUILD_FRAMEWORK') )

	# Reads version number in VERSION file
	versionFile	= os.path.join(sbfRoot, 'VERSION')
	if os.path.lexists( versionFile ) :
		with open( versionFile ) as file :
			return file.readline()
	else :
		return "Missing {0} file. So version number is unknown.".format(versionFile)



### Helpers to split 'uses' value ###
usesNamePattern = '(?P<name>[a-zA-Z]+(?:[\d][a-zA-Z]+|))'
usesVersionPattern = '(?P<version>[\d-]*)'

def splitUsesName( singleUsesValue ):
	"""@return (name, version) from 'nameVersion', 'name' or 'name version'.
	@remark Example: splitUses( 'boost1-48-0' ) returns ('boost', '1-48-0')"""

	splitter = re.compile( r'^{0}[ \t]*{1}'.format(usesNamePattern, usesVersionPattern) )
	match = splitter.match( singleUsesValue )
	if match:
		return match.groups()
	else:
		raise SCons.Errors.UserError("uses=['{0}']. The following schemas must be used ['nameVersion'], ['name'] or ['name version'].".format(name) )

#print splitUsesName('opengl')
#print splitUsesName('boost1-48-0')
#print splitUsesName('usb2brd1-0')

### Helpers to split package name ###
packagePlatform = '(?P<platform>.+)'
packageCC = '(?P<cc>.+)'
packageExtension = '(?P<extension>.+)'

def splitPackageName( packageName ):
	"""@remark Example: splitPackageName( 'opencollada865_win32_cl10-0Exp.zip' ) returns 
	{	'name'		: 'opencollada',
		'version'	: '865',
		'platform'	: 'win32',
		'cc'		: 'cl10-0Exp',
		'extension'	: 'zip' }"""
	splitter = re.compile( r'^{0}{1}_{2}_{3}[.]{4}$'.format( usesNamePattern, usesVersionPattern, packagePlatform, packageCC, packageExtension ) )
	match = splitter.match( packageName )
	if match:
		return {	'name'		: match.group('name'),
					'version'	: match.group('version'),
					'platform'	: match.group('platform'),
					'cc'		: match.group('cc'),
					'extension'	: match.group('extension') }
	else:
		#print ("Unable to split package name {0}. The following schemas must be used 'nameVersion_platform_ccVersion.extension'.".format(packageName) )
		return

def joinPackageName( pakInfo ):
	"""@remark Example: tmp = {
		'name'		: 'opencollada',
		'version'	: '865',
		'platform'	: 'win32',
		'cc'		: 'cl10-0Exp',
		'extension'	: 'zip' }
		joinPackageName(tmp) returns 'opencollada865_win32_cl10-0Exp.zip'
	"""
	return "{0}{1}_{2}_{3}.{4}".format( pakInfo['name'], pakInfo['version'], pakInfo['platform'], pakInfo['cc'], pakInfo['extension'] )
