#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, 2011, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import datetime
import logging
import os
import pysvn
import sys
from os.path import join

from sbfPaths import Paths
from sbfEnvironment import Environment

# @todo takes care of PATH for machine (not only PATH for current user).
# @todo posix version

def directoryInput( text, defaultValue ):
	while( True ):
		directory = raw_input( text + ' ' )
		if len(directory) == 0:
			directory = defaultValue
		directory_normalized = os.path.normpath( os.path.expandvars( directory ) )
		if not os.path.exists(directory_normalized):
			answer = raw_input('Creates directory %s\n no or the default choice (y)es ?'% directory_normalized )
			if answer in ['y', '']:
				os.makedirs( directory_normalized )
				return directory_normalized
			else:
				continue
		else:
			logging.info( 'Directory %s already exists' % directory_normalized )
			#print ( 'Directory %s already exists' % directory_normalized )
			return directory_normalized


def svnCallback_ssl_server_trust_prompt( trust_dict ):
	print ("Error validating server certificate for '%s':" % trust_dict['realm'] )
	print (' - The certificate is not issued by a trusted authority.')
	print ('   Use the fingerprint to validate the certificate manually !')
	print ('Certificate informations:')
	print (' - Hostname: %s' %		trust_dict['hostname'] )
	print (' - Fingerprint: %s' %	trust_dict['finger_print'] )
	print (' - Valid from: %s' %	trust_dict['valid_from'] )
	print (' - Valid until: %s' %	trust_dict['valid_until'] )
	print (' - Issuer: %s' %		trust_dict['issuer_dname'] )

	trust	= True
	save	= True

	return trust, trust_dict['failures'], save

def svnCheckoutOrUpdateSBF( path, action ):
	"""action must be 'checkout' or 'update' to choose svn checkout or svn update"""
	cwdSaved = os.getcwd()
	os.chdir( path )

	client = pysvn.Client()
	client.set_interactive( True )
	client.exception_style = 1
	client.callback_ssl_server_trust_prompt = svnCallback_ssl_server_trust_prompt
	try:
		if action == 'checkout':
			urlForCheckout = 'http://sbf.googlecode.com/svn/trunk/'
			logging.info( 'Retrieves (using svn checkout) sbf from {0} in {1}'.format(urlForCheckout, path) )
			print ( 'Retrieves (using svn checkout) sbf {0} in {1}'.format(urlForCheckout, path) )
			client.checkout( urlForCheckout, '.' )
			return True
		else:
			logging.info( 'Retrieves (using svn update) sbf in {0}'.format(path) )
			print ( 'Retrieves (using svn update) sbf in {0}'.format(path) )
			client.update( path )
			return True
	except pysvn.ClientError, e :
		logging.error(e.args[0], '\n')
		print e.args[0], '\n'
		return False
	finally:
		os.chdir( cwdSaved )


SConsBuildFramework_optionsString = """numJobs = %s
pakPaths = [ 'V:\\Dev\\localExt', 'V:\\Dev\\localExt_win32_cl9-0' ]

# to authenticate check out the source code using your login:
#	'svn+ssh://login@orange/srv/svn/lib/{PROJECT}/trunk' or
#	'https://vgsdk.googlecode.com/svn/trunk'
#
# to anonymously check out the source code:
#	'svn://orange/srv/svn/lib/{PROJECT}/trunk'
#	'http://vgsdk.googlecode.com/svn/trunk'
#
svnUrls = { 'displayDriverConnector'	: 'http://oglpp.googlecode.com/svn/displayDriverConnector/trunk',
			'glContext'					: 'http://oglpp.googlecode.com/svn/glContext/trunk',
			'gle'						: 'http://oglpp.googlecode.com/svn/gle/trunk',
			'glo'	    				: 'http://oglpp.googlecode.com/svn/glo/trunk',
			'vgsdk'						: 'http://vgsdk.googlecode.com/svn/trunk',
			'' : [ 'svn://orange/srv/svn/lib/{PROJECT}/trunk', 'svn://orange/srv/svn/bin/{PROJECT}/trunk', 'svn://orange/srv/svn/share/{PROJECT}/trunk' ] }

#projectExclude		= [ '*/vgsdk*' ]
weakLocalExtExclude = ['sofa'] # to avoid cleaning projects at each sofa update.
clVersion = '2008Exp'

installPaths = ['%s']
buildPath    = '%s'


#from src.SConsBuildFramework import createBlowfishShareBuildCommand
#userDict =	{ 'blowfish' : createBlowfishShareBuildCommand( 'theKey' ) }
"""


#
#raw_input('Start execution of SConsBuildFramework bootstrap script. Press return.\n')

# *** Creates installation log file ***
myDate = str(datetime.datetime.today().strftime("%Y-%m-%d_%Hh%Mm%Ss"))
logFilename = 'sbf-wininst_%s.log'% myDate
logging.basicConfig(filename=logFilename, level=logging.DEBUG,)
print ("Creates installation log file %s" % logFilename )
print

# *** Sets SCONS_BUILD_FRAMEWORK environment variable ***
environment = Environment()
logging.info('\n------ Sets SCONS_BUILD_FRAMEWORK environment variable')
print ('\n------ Sets SCONS_BUILD_FRAMEWORK environment variable\n')

 # defines sbf_root
sbf_root = environment.get( 'SCONS_BUILD_FRAMEWORK' )
if sbf_root == None or len(sbf_root) == 0 :
	sbf_root = r'D:\\Dev\\bin\\SConsBuildFramework'
else:
	sbf_root = os.path.normpath( os.path.expandvars( os.path.abspath(sbf_root) ) )
	sbf_root = sbf_root.replace( '\\', '\\\\' )

print
sbf_root = directoryInput( 'SCONS_BUILD_FRAMEWORK root directory (default: {0}) ? '.format(sbf_root), sbf_root )
sbf_root = os.path.normpath( os.path.expandvars( os.path.abspath(sbf_root) ) )

environment.set( 'SCONS_BUILD_FRAMEWORK', sbf_root )
SCONS_BUILD_FRAMEWORK = sbf_root #environment.get( 'SCONS_BUILD_FRAMEWORK', False ) # = sbf_root DEBUG @todo removeme
print

# *** Check out or update the current version of the sbf project ***

# @todo improves this test => isUnderSvn()
if os.path.exists( join(SCONS_BUILD_FRAMEWORK, 'sbfMain.py' ) ):
	logging.info('\n------ svn update')
	print ('\n------ svn update\n')
	logging.info( 'SConsBuildFramework is already checkout in %s ' % SCONS_BUILD_FRAMEWORK )
	print ( 'SConsBuildFramework is already checkout in %s ' % SCONS_BUILD_FRAMEWORK )
	svnCheckoutOrUpdateSBF( SCONS_BUILD_FRAMEWORK, 'update' )
else:
	logging.info('\n------ svn checkout')
	print ('\n------ svn checkout\n')
	svnCheckoutOrUpdateSBF( SCONS_BUILD_FRAMEWORK, 'checkout' )
print

# *** Creates SConsBuildFramework.options ***
logging.info('\n------ Writes the main configuration file of sbf (SConsBuildFramework.options)')
print ('\n------ Writes the main configuration file of sbf (SConsBuildFramework.options)\n')

sysPathBak = sys.path
sys.path = [SCONS_BUILD_FRAMEWORK] + sys.path[1:]

sbf_options = join( SCONS_BUILD_FRAMEWORK, 'SConsBuildFramework.options' )

sbfConfigFileContent = []
sbfConfigFileDict = {}
if os.path.exists( sbf_options ):
	# Reads the sbf configuration
	with open( sbf_options ) as file:
		sbfConfigFileContent = file.readlines()

	# Creates a backup of the sbf configuration
	backup = 'SConsBuildFramework.options_' + myDate + '.backup.txt'
	logging.info( 'Backups SConsBuildFramework.options into %s' % backup )
	print( 'Backups SConsBuildFramework.options into %s' % backup )
	with open( sbf_options, 'w' ) as file:
		file.writelines( sbfConfigFileContent )

	# Retrieves sbf configuration (only several values)
	# @todo full
	try:
		execfile( sbf_options, {}, sbfConfigFileDict )
	except SyntaxError as e:
		print ('Syntax error in {0}'.format(sbf_options))
		logging.info('Syntax error in {0}'.format(sbf_options))
		print e
		logging.info(e)
		pass
	except ImportError as e:
		logging.info('ERROR.\nYour sbf configuration file ({0}) contains at least one error.'.format(sbf_options))
		print ('ERROR.\nYour sbf configuration file ({0}) contains at least one error.'.format(sbf_options))
		print e
		logging.info(e)
		pass
		#print sbfConfigFileDict.get('numJobs', 'nop')
		#print sbfConfigFileDict.get('installPaths', 'nop')
		#print sbfConfigFileDict.get('buildPath','nop')
		#import pprint
		#pprint.pprint(sbfConfigFileDict['svnUrls'], logging.handler())

# @todo Asks numJobs
# @todo non win32 and non existence for NUM_OF_PROC
numJobs			= sbfConfigFileDict.get( 'numJobs', os.getenv('NUMBER_OF_PROCESSORS') )
print

defaultPath = sbfConfigFileDict.get( 'installPaths', [r'd:\\local'] )[0]
sbfLocalPath	= directoryInput( 'sbf local directory {0} ? '.format(defaultPath) , defaultPath )
print

defaultPath = sbfConfigFileDict.get( 'buildPath', r'd:\\tmp\\sbf\\build' )
sbfTmpPath		= directoryInput( 'sbf tmp directory {0} ? '.format(defaultPath), defaultPath )
print

with open( sbf_options, 'w' ) as file :
	# Writes new SConsBuildFramework.options file
	logging.info( 'Writes %s' % sbf_options )
	print ( 'Writes %s' % sbf_options )
	tmp = SConsBuildFramework_optionsString % (numJobs, sbfLocalPath, sbfTmpPath)
	if sys.platform == 'win32':
		file.write( tmp.replace( '\\', '\\\\' ) )
	# Appends the previous SConsBuildFramework.options file
	file.write('\n\n' + '#'*79 + '\n')
	file.write('Below, your previous SConsBuildFramework.options.\n')
	file.write('You must manually reintegrate it.\n\n')
	file.writelines(sbfConfigFileContent)
print

# *** Gets PATH, saves path.txt and updates PATH ***
logging.info('\n------ Updates PATH')
print ('\n------ Updates PATH\n')

# gets
PATH = environment.get( 'PATH' )

# backups PATH environment variable
backup = join( SCONS_BUILD_FRAMEWORK, 'PATH_%s.backup.txt' % myDate )
with open( backup, 'w' ) as file :
	logging.info( 'Backups PATH in %s' % backup )
	print ( 'Backups PATH in %s' % backup )
	file.write( 'PATH=%s' % PATH )
print

# updates PATH
paths = Paths( PATH )

from src.sbfTools import locateProgram

# see SbfMain.py: _getSBFRuntimePaths() # @todo shared code
prependList = []
appendList  = []
# Prepends $SCONS_BUILD_FRAMEWORK in PATH for 'scons' file containing scons.bat $*
prependList.append( SCONS_BUILD_FRAMEWORK )

# Adds C:\PythonXY (where C:\PythonXY is the path to your python's installation directory) to your PATH environment variable.
# This is important to be able to run the Python executable from any directory in the command line.
pythonLocation = locateProgram('python')
appendList.append( pythonLocation )

# Adds c:\PythonXY\Scripts (for scons.bat)
appendList.append( join(pythonLocation, 'Scripts') )

#
paths.prependList( prependList, True )
paths.appendList( appendList, True )

#
environment.set( 'PATH', paths.getString() )
print

#
raw_input('Finish execution of SConsBuildFramework bootstrap script. Press return.\n')
