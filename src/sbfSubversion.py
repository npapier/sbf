# SConsBuildFramework - Copyright (C) 2005, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import atexit, fnmatch, glob, re, sys

# pysvn must be installed
try:
	import pysvn
except ImportError as e:
	print ('sbfWarning: pysvn is not installed.')
	raise e

import os
from os.path import basename, dirname, exists, isfile, isdir, join, normpath, relpath
from sbfIVersionControlSystem import IVersionControlSystem
from sbfFiles import convertPathAbsToRel
from sbfTools import locateProgram



# @todo try to limit self.sbf
# @todo svnSwitch => svn switch
# svnLogIncoming
# @todo a global atexit (see SCons ?)
# @todo commit, merge, mergeinfo
# @todo replaces convertPathAbsToRel by relpath ?
# @todo isBuildNeeded() => buildbot
# @todo create/applyPatch
#def fmtDateTime( t ):
#	import time
#	return time.strftime( '%d-%b-%Y %H:%M:%S', time.localtime( t ) )



### Statistics ###
class Statistics:
	def __init__( self ):
		self.reset()

	def reset( self ):
		# details[type] = count
		self.details			= {}
		# addFileCounter[fileType] = count
		self.addFileCounter		= {}
		# copyFileCounter[fileType] = count
		self.copyFileCounter	= {}
		# deleteFileCounter[fileType] = count
		self.deleteFileCounter	= {}
		#
		self.conflicted	= []
		self.merged		= []

	def increments( self, type ):
		self.details[type] = self.details.get(type, 0) + 1


	def incrementsAddFile( self, type ):
		self.addFileCounter[type] = self.addFileCounter.get(type, 0) + 1

	def incrementsCopyFile( self, type ):
		self.copyFileCounter[type] = self.copyFileCounter.get(type, 0) + 1

	def incrementsDeleteFile( self, type ):
		self.deleteFileCounter[type] = self.deleteFileCounter.get(type, 0) + 1


	def addConflicted( self, projectPath, pathFilename ):
		self.conflicted.append( (projectPath, pathFilename) )

	def addMerged( self, projectPath, pathFilename ):
		self.merged.append( (projectPath, pathFilename) )

	def printReport( self ):
		if len(self.details) + len(self.conflicted) + len(self.merged) > 0 :
			print 'svn report:',

		for (k,v) in self.details.iteritems():
			print ('%s:%i' %(k,v) ),
		if len(self.details) > 0:
			print

		def report( dict, text ):
			report = ''
			for (k,v) in dict.iteritems():
				report += '%s:%i ' % (k,v)
			if len(report) > 0:
				print '{0}: {1}'.format(text, report)

		# add
		report( self.addFileCounter, 'add' )

		# copy
		report( self.copyFileCounter, 'copy' )

		# delete
		report( self.deleteFileCounter, 'delete' )

		#
		if len(self.conflicted) > 0:
			print 'conflicted:'
			for (projectPath, pathFilename) in self.conflicted:
				print convertPathAbsToRel(projectPath, pathFilename)
			print

		if len(self.merged) > 0:
			print 'merged:'
			for (projectPath, pathFilename) in self.merged:
				print convertPathAbsToRel(projectPath, pathFilename)


##### Low-level pysvn ######

def splitSvnUrl( svnUrl, projectName = '{PROJECT}' ):
	"""Returns (url, revision) from svnUrl. {PROJECT} sub-string in svnUrl would be replaced by given projectName.
	# Returns :
	# - (file:///D:/tmp/dev-branch/srv/svn/bin/{PROJECT}/trunk, None) for file:///D:/tmp/dev-branch/srv/svn/bin/{PROJECT}/trunk
	# - (file:///D:/tmp/dev-branch/srv/svn/bin/{PROJECT}/trunk, 3050) for file:///D:/tmp/dev-branch/srv/svn/bin/{PROJECT}/trunk@3050
	# - (file:///D:/tmp/dev-branch/srv/svn/bin/{PROJECT}/branches/2.0, 3058) for file:///D:/tmp/dev-branch/srv/svn/bin/{PROJECT}/branches/2.0@3058
	# - (svn+ssh://npapier@orange/srv/svn/lib/{PROJECT}/trunk, 3000) for svn+ssh://npapier@orange/srv/svn/lib/{PROJECT}/trunk@3000
	# - (https://vgsdk.googlecode.com/svn/trunk, None) for https://vgsdk.googlecode.com/svn/trunk"""

	# endOfSvnUrl = '/trunk@3000' or '/trunk'
	endOfSvnUrl = svnUrl[svnUrl.rindex('/'):]
	hasRevisionNumber = ( endOfSvnUrl.rfind('@') != -1 )
	if hasRevisionNumber:
		atLocation = svnUrl.rfind('@')
		url = svnUrl[:atLocation].format(PROJECT=projectName)
		revision = svnUrl[atLocation+1:]
	else:
		url = svnUrl.format(PROJECT=projectName)
		revision = None
	return (url, revision)

def joinSvnUrl( svnUrl, revision ):
	return svnUrl + '@' + revision

def printRevision( myProject, revisionNumber ):
	print ("{0} at revision {1}".format(myProject, revisionNumber))

#@todo uses sbfUI and debug 'accept temporarily'
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

	print
	while( True ):
		userChoice = raw_input('(R)eject, accept (t)emporarily(@todo buggy) or accept (p)ermanently ?')		# @todo (t)emporarily seems to be buggy => pysvn ?
		userChoice = userChoice.lower()

		if userChoice in ['r', 't', 'p'] :
			break

	trust	= userChoice in ['t', 'p']
	save	= (userChoice == 'p')

	return trust, trust_dict['failures'], save


#@todo uses sbfUI
def svnCallback_get_login( realm, username, may_save ):
	print ('Authentication realm: %s' % realm)

	givenUsername = raw_input('Username (%s):' % username)
	if len(givenUsername) == 0:
		givenUsername = username

	givenPassword = raw_input("Password for '%s':" % givenUsername)

	return (len(givenUsername) != 0) and (len(givenPassword) != 0), givenUsername, givenPassword, True


class CallbackNotifyWrapper:
	wcNotifyActionMap = {
		pysvn.wc_notify_action.add:						'A',
		pysvn.wc_notify_action.copy:					'c',
		pysvn.wc_notify_action.delete:					'D',
		pysvn.wc_notify_action.restore:					'R',
		pysvn.wc_notify_action.revert:					'R',
		pysvn.wc_notify_action.failed_revert:			'F',
		pysvn.wc_notify_action.resolved:				'R',
		pysvn.wc_notify_action.skip:					'?',
		pysvn.wc_notify_action.update_delete:			'D',
		pysvn.wc_notify_action.update_add:				'A',
		pysvn.wc_notify_action.update_update:			'U',
		pysvn.wc_notify_action.update_completed:		None,
		pysvn.wc_notify_action.update_external:			'E',
		pysvn.wc_notify_action.status_completed:		None,
		pysvn.wc_notify_action.status_external:			'E',
		pysvn.wc_notify_action.commit_modified:			'M',
		pysvn.wc_notify_action.commit_added:			'A',
		pysvn.wc_notify_action.commit_deleted:			'D',
		pysvn.wc_notify_action.commit_replaced:			'R',
		pysvn.wc_notify_action.commit_postfix_txdelta:	None,
		pysvn.wc_notify_action.annotate_revision:		'a',
		pysvn.wc_notify_action.locked:					None,
		pysvn.wc_notify_action.unlocked:				None,
		pysvn.wc_notify_action.failed_lock:				None,
		pysvn.wc_notify_action.failed_unlock:			None,
	}


	def __init__( self, rootPath = '', statisticsObservers = []):
		"""	@param rootPath					typically the root directory of the current project.
			@param statisticsObservers		list of Statistics instances that must be updated"""
		self.rootPath = rootPath
		self.statisticsObservers = set(statisticsObservers)


	def setRootPath( self, rootPath ):
		self.rootPath = rootPath


	def attach( self, statistics ):
		self.statisticsObservers.add( statistics )

	def detach( self, statistics ):
		if statistics in self.statisticsObservers:
			self.statisticsObservers.remove( statistics )


	def __call__( self, eventDict ):
		self.__callbackNotify( eventDict )

	def __callbackNotify( self, eventDict ):
		path = eventDict['path']
		if len(path) == 0 :
			# empty path, nothing to do
			return

		action = eventDict['action']

		if (action in self.wcNotifyActionMap and (self.wcNotifyActionMap[action] is not None)					# known action that must trigger a message
		and not (action == pysvn.wc_notify_action.update_update and eventDict['kind'] == pysvn.node_kind.dir)	# but not in this special case
		):
			lookupAction = self.wcNotifyActionMap[action]

			# Checks if there is a conflict
			contentState = eventDict['content_state']
# @todo checks in depth wc_notify_state => M(erge)
			if contentState == pysvn.wc_notify_state.merged :
				lookupAction = 'G'
				for statistics in self.statisticsObservers:
					statistics.addMerged(self.rootPath, path )
			elif contentState == pysvn.wc_notify_state.conflicted :
				# Overridden self.wcNotifyActionMap[] result
				lookupAction = 'C'
				for statistics in self.statisticsObservers:
					statistics.addConflicted( self.rootPath, path )

			# Updates statistics
			for statistics in self.statisticsObservers:
				statistics.increments( lookupAction )
				#
				extension = os.path.splitext(basename(path))[1]
				# add
				if lookupAction is 'A': statistics.incrementsAddFile( extension )
				if lookupAction is 'c': statistics.incrementsCopyFile( extension )
				if lookupAction is 'D': statistics.incrementsDeleteFile( extension )

			print lookupAction, "\t",
			if len(self.rootPath) > 0:
				print convertPathAbsToRel( self.rootPath, path )
			else:
				print path


class CallbackGetLogMessage:
	def __init__( self, message = ''):
		self.message = message

	def setMessage( self, message ):
		self.message = message

	def __call__( self ):
		if len(self.message)==0:
			return False, ''
		else:
			return True, self.message

# List of classes encapsulating pysvn operation(s)
# abstract SvnOperation
# SvnGetInfo, SvnGetRevision, svnGetUUID
# SvnList, SvnListDirectory, SvnListFile
# SvnGetWorkingAndRepositoryRevision, SvnUpdateAvailable
# svnIsUnversioned, svnIsVersioned
# SvnAddFileOrDir, SvnAddDirs
# SvnMkDir, SvnRemove
# SvnCheckout, SvnExport, SvnUpdate, SvnCat
# SvnRelocate
# SvnCopy
# (SvnStatus, SvnRemoteStatus @todo)



# SvnOperation
class SvnOperation:
	"""Encapsulation of svn operation(s) using pysvn."""

	def __init__( self, rootPath = '', statisticsObservers = [] ):
		"""	@param rootPath				see CallbackNotifyWrapper()
			@param statisticsObservers	see CallbackNotifyWrapper()

			@todo OPTME adds a client parameter __init__()"""

		# self.rootPath
		self.rootPath = rootPath

		# self.client
		# Creates and configures pysvn client
		client = pysvn.Client()
		client.callback_notify						= CallbackNotifyWrapper( rootPath, statisticsObservers )
		client.callback_ssl_server_trust_prompt		= svnCallback_ssl_server_trust_prompt
		client.callback_get_login					= svnCallback_get_login
		client.callback_get_log_message				= CallbackGetLogMessage()
		client.exception_style						= 1

		self.client = client

		# self.statistics
		# Creates my own instance of Statistics and attaches to client
		self.statistics = Statistics()

	def __call__( self, *args ):
		try:
			self.client.callback_notify.attach( self.statistics )
			retVal = self.doSvnOperation( *args )
			self.client.callback_notify.detach( self.statistics )
			return retVal
		except pysvn.ClientError as e:
			self.printErrorMessages(e)
			exit(1)

	def doSvnOperation( self, *args ):
		raise AssertionError( '{0}::doSvnOperation() not implemented.'.format(self) )

	def setLogMessage( self, logMessage ):
		self.client.callback_get_log_message.setMessage( logMessage )

	def printStatisticsReport( self ):
		self.statistics.printReport()

	def printErrorMessages( self, e ):
		print ('An error occurs during an svn operation:')
		print ('{0}\n'.format(e.args[0]))
		#print e.args[1]


# SvnGetInfo, SvnGetRevision, svnGetUUID
class SvnGetInfo( SvnOperation ):
	"""SvnGetInfo()(urlOrPath)
		@param urlOrPath	path of the current working copy or url of the repository
		@return None if not under vcs, otherwise returns the desired info (i.e. info_dict)
		@see http://pysvn.tigris.org/docs/pysvn_prog_ref.html#pysvn_client_info2"""

	def doSvnOperation( self, *args ):
		# argument
		urlOrPath = args[0]

		# do
		try:
			entry_list = self.client.info2( urlOrPath, depth = pysvn.depth.empty )
			if len(entry_list)==1:
				infoDict = entry_list[0][1]
				return infoDict
			else:
				print ('entry_list=', entry_list)
				raise AssertionError('len(entry_list)!=1')
		except pysvn.ClientError as e:
			#print e[0]
			#print e[1]
			#e[0] whole message
			#e[1] = list((msg str,error code)
			if len(e[1])==1:
				errorCode = e[1][0][1]
				if errorCode in [155007, 155010, 170000, 200005]:
					# 155007 : "'path' is not a working copy"
					# 155010 : "The node 'path' was not found."
					# 170000 : "URL 'url' non-existent in revision REVNUM
					# 200005 : "'path' is not under version control"
					return
				else:
					raise e
			else:
				assert( len(e[1]) > 1 )
				raise e
				#self.printErrorMessages(e)


class SvnGetRevision( SvnGetInfo ):
	"""SvnGetRevision()(urlOrPath)
		@param urlOrPath	path of the current working copy or url of the repository
		@return None if not under vcs, otherwise returns the revision number"""

	def doSvnOperation( self, *args ):
		retVal = SvnGetInfo.doSvnOperation( self, *args )
		if retVal:
			return retVal['rev'].number


class SvnGetUUID( SvnGetInfo ):
	"""SvnGetUUID()(urlOrPath)
		@param urlOrPath	path of the current working copy or url of the repository
		@return None if not under vcs, otherwise returns the repository UUID"""

	def doSvnOperation( self, *args ):
		retVal = SvnGetInfo.doSvnOperation( self, *args )
		if retVal:
			return retVal['repos_UUID']


# SvnList, SvnListDirectory, SvnListFile
class SvnList( SvnOperation ):
	"""SvnList()( urlOrPath, depth, pattern = '*', revisionNumber = None )
		@brief Returns a list of each file/directory in the given urlOrPath at the provided revision.
		@param urlOrPath		path of the current working copy or url of the repository
		@param depth			one of the pysvn.depth enumeration values
		@param pattern			the returned list contains only element matching this pattern (default value is '*')
		@param revisionNumber	None for head or a number for a specific revision (default value is None)
		@return a list of files and directories"""

	def __call__( self, urlOrPath, depth, pattern = '*', revisionNumber = None ):
		return SvnOperation.__call__(self, urlOrPath, depth, pattern, revisionNumber)

	def doSvnOperation( self, *args ):
		# arguments
		urlOrPath = args[0]
		depth = args[1]
		pattern = args[2]
		if args[3]:
			revision = pysvn.Revision( pysvn.opt_revision_kind.number, args[3] )
		else:
			revision = pysvn.Revision( pysvn.opt_revision_kind.head )

		# do
		entries = self.client.list( urlOrPath, revision=revision, dirent_fields=pysvn.SVN_DIRENT_KIND, depth=depth )
		filteredEntries = [ entry for entry in entries if fnmatch.fnmatch(entry[0].path, pattern) ]
		return filteredEntries


class SvnListDirectory( SvnList ):
	"""SvnListDirectory()( urlOrPath, depth, pattern = '*', revisionNumber = None )
		See SvnList for explanation.
		@return a list of directories"""

	def __call__( self, urlOrPath, depth, pattern = '*', revisionNumber = None ):
		return SvnList.__call__(self, urlOrPath, depth, pattern, revisionNumber)

	def doSvnOperation( self, *args ):
		urlOrPath = args[0]

		#
		entries = SvnList.doSvnOperation( self, *args )
		retVal = []
		for entry in entries:
			if entry[0].kind == pysvn.node_kind.dir:
				newElement = entry[0].path.replace(urlOrPath, '', 1).lstrip('/')
				if len(newElement)>0:
					retVal.append(newElement)
		return retVal


class SvnListFile( SvnList ):
	"""SvnListFile()( urlOrPath, depth, pattern = '*', revisionNumber = None )
		See SvnList for explanation.
		@return a list of files"""

	def __call__( self, urlOrPath, depth, pattern = '*', revisionNumber = None ):
		return SvnList.__call__(self, urlOrPath, depth, pattern, revisionNumber)

	def doSvnOperation( self, *args ):
		urlOrPath = args[0]

		#
		entries = SvnList.doSvnOperation( self, *args )
		retVal = []
		for entry in entries:
			if entry[0].kind == pysvn.node_kind.file:
				newElement = entry[0].path.replace(urlOrPath, '', 1).lstrip('/')
				retVal.append(newElement)
		return retVal


# SvnGetWorkingAndRepositoryRevision, SvnGetWorkingAndRepositoryLastChangedRevision, SvnGetWorkingAndRepositoryRevisionAndLastChangedRevision, SvnUpdateAvailable
class SvnGetWorkingAndRepositoryRevision( SvnGetInfo ):
	"""SvnGetWorkingAndRepositoryRevision()( workingCopyPath )
		@param workingCopyPath	path to the current working copy
		@return None if not under vcs, otherwise returns (workingRevisionNumber, repositoryRevisionNumber)"""

	def doSvnOperation( self, *args ):
		workingInfo = SvnGetInfo.doSvnOperation( self, *args )
		if workingInfo:
			repositoryInfo = SvnGetInfo.doSvnOperation( self, workingInfo['URL'] )
			if repositoryInfo:
				return (workingInfo['rev'].number, repositoryInfo['rev'].number)


class SvnGetWorkingAndRepositoryLastChangedRevision( SvnGetInfo ):
	"""SvnGetWorkingAndRepositoryLastChangedRevision()( workingCopyPath )
		@param workingCopyPath	path to the current working copy
		@return None if not under vcs, otherwise returns (workingLastChangedRevisionNumber, repositoryLastChangedRevisionNumber)"""

	def doSvnOperation( self, *args ):
		workingInfo = SvnGetInfo.doSvnOperation( self, *args )
		if workingInfo:
			repositoryInfo = SvnGetInfo.doSvnOperation( self, workingInfo['URL'] )
			if repositoryInfo:
				return (workingInfo['last_changed_rev'].number, repositoryInfo['last_changed_rev'].number)


class SvnGetWorkingAndRepositoryRevisionAndLastChangedRevision( SvnGetInfo ):
	"""SvnGetWorkingAndRepositoryRevisionAndLastChangedRevision()( workingCopyPath )
		@param workingCopyPath	path to the current working copy
		@return None if not under vcs, otherwise returns (workingRevisionNumber, repositoryRevisionNumber, workingLastChangedRevisionNumber, repositoryLastChangedRevisionNumber)"""

	def doSvnOperation( self, *args ):
		workingInfo = SvnGetInfo.doSvnOperation( self, *args )
		if workingInfo:
			repositoryInfo = SvnGetInfo.doSvnOperation( self, workingInfo['URL'] )
			if repositoryInfo:
				return (workingInfo['rev'].number, repositoryInfo['rev'].number, workingInfo['last_changed_rev'].number, repositoryInfo['last_changed_rev'].number)


# @todo Improves SvnUpdateAvailable() => retVal = SvnStatus(), checks len(retVal) and retVal contents
class SvnUpdateAvailable( SvnGetWorkingAndRepositoryRevision ):
	"""SvnUpdateAvailable()( workingCopyPath )
		@param workingCopyPath	path to the current working copy
		@return None if not under vcs, otherwise returns True if there is an update available, False if not"""

	def doSvnOperation( self, *args ):
		retVal = SvnGetWorkingAndRepositoryRevision.doSvnOperation( self, *args )
		if retVal:
			workingRev = retVal[0];
			repositoryRev = retVal[1]
			return workingRev < repositoryRev


# svnIsUpdateAvailable
def svnIsUpdateAvailable( path, desiredRevisionNumber, verbose = True, veryVerbose = False, callExitOnError = True ):
	"""	@param path						the path to the project to test
		@param desiredRevisionNumber	a revision number or None for latest revision"""

	if desiredRevisionNumber:	desiredRevisionNumber = int(desiredRevisionNumber)

	project = basename(path)
	if exists(path):
		# existing path
		if svnIsVersioned(path):
			(workingRevisionNumber, repositoryRevisionNumber, workingLastChangedRevisionNumber, repositoryLastChangedRevisionNumber) = SvnGetWorkingAndRepositoryRevisionAndLastChangedRevision()( path )
			if veryVerbose:
				print ("Last changed of working copy at revision {0} for {1}, last changed of remote version at revision {2}.".format(workingLastChangedRevisionNumber, project, repositoryLastChangedRevisionNumber))
				print ("Working copy of {0} at revision {1}, remote version at revision {2}.".format(project, workingRevisionNumber, repositoryRevisionNumber))
			if desiredRevisionNumber:
				# update to revision
				if workingRevisionNumber < desiredRevisionNumber:
					if desiredRevisionNumber > repositoryRevisionNumber:
						print ('WARNING:Unable to update {0} to revision {1}. Latest revision available is {2}.'.format(project, desiredRevisionNumber, repositoryRevisionNumber))
						if callExitOnError:
							exit(1)
						else:
							return False
					# else nothing to do
					if verbose:	print ('REVISION {revisionNumber} IS AVAILABLE FOR {project}.'.format( revisionNumber=desiredRevisionNumber, project=project.upper() ) )
					return True
				elif workingRevisionNumber == desiredRevisionNumber:
					if verbose:	print ( '{project} at revision {revision}.'.format( project=project, revision=desiredRevisionNumber ) )
					if veryVerbose:	print ( '{project} is up-to-date.'.format(project=project) )
					return False
				else:
					assert( workingRevisionNumber > desiredRevisionNumber )
					if verbose:	print ('{project} is newer than the desired revision {revision}.'.format(project=project, revision=desiredRevisionNumber) )
					return True
			else:
				# update to latest
				if workingLastChangedRevisionNumber < repositoryLastChangedRevisionNumber:
					if verbose:	print ('REVISION {revisionNumber} IS AVAILABLE FOR {project}.'.format( revisionNumber=repositoryLastChangedRevisionNumber, project=project.upper() ) )
					return True
				else:
					assert( workingLastChangedRevisionNumber == repositoryLastChangedRevisionNumber )
					if verbose:	print ( '{project} at revision {revision}.'.format( project=project, revision=workingLastChangedRevisionNumber ) )
					if veryVerbose:	print ( '{project} is up-to-date.'.format(project=project) )
					return False
		else:
			if verbose:	print ('{project} is not under vcs.'.format(project=project))
			if callExitOnError:
				exit(1)
			else:
				return False
	else:
		# path is not an existing path, an update is available (first checkout).
		if verbose:	print ( '{project} not found.'.format(project=project) )
		return True

# svnIsUnversioned, svnIsVersioned
def svnIsUnversioned( urlOrPath ):
	revision = SvnGetRevision()(urlOrPath)
	return revision == None


def svnIsVersioned( urlOrPath ):
	return not svnIsUnversioned(urlOrPath)


# SvnAddFileOrDir, SvnAddDirs
# SvnMkDir, SvnRemove
class SvnAddFileOrDir( SvnOperation ):
	"""	SvnAddFileOrDir()(path)
		@pre dirname(path) must be under svn

		@todo pysvn seems to be unaware of svn:ignore properties. pysvn bug or wrong pysvn usage ?"""

	def __isInIgnoreList( self, file, ignoreList ):
		for ignore in ignoreList:
			#print ('checks', file, ignore)
			if fnmatch.fnmatch(file, ignore):
				return True
		return False

	def doSvnOperation( self, *args ):
		# argument
		path = args[0]

		# do
		file = basename(path)
		svnIgnorePropDict = self.client.propget( 'svn:ignore', dirname(path) )

		for svnIgnoreProp in svnIgnorePropDict.values():
			svnIgnorePropList = svnIgnoreProp.rstrip('\n').split('\n')
			
			if self.__isInIgnoreList( file, svnIgnorePropList ):
				# Must be ignored
				#print('I{0}'.format(path))
				return False
		self.client.add( path, depth=pysvn.depth.empty )
		return True


class SvnAddDirs( SvnOperation ):
	"""SvnAddDirs()(path, start)
		Adds recursively 'path' under svn from its parent path 'start'.
		@pre start must be under svn"""

	def doSvnOperation( self, *args ):
		# arguments
		path = args[0]
		start = args[1]

		# do
		currentPath = start
		for newPathElement in relpath(path, start).split( os.sep ):
			currentPath = join( currentPath, newPathElement )
			if svnIsUnversioned( currentPath ):
				# not under svn, so must be added
				if not SvnAddFileOrDir(rootPath=self.rootPath)( currentPath ):
					return False
			#else nothing to do
		return True


class SvnMkDir( SvnOperation ):
	"""SvnMkDir()(urlOrPath, logMessage, [makeParents]=True)
		Creates a new directory under revision control.
		@param urlOrPath	If urlOrPath is a path, each directory is scheduled for addition upon the next commit.
							If urlOrPath is a URL, the directories are created in the repository via an immediate commit.
		@param makeParents	all the intermediate directories must already exist when makeParents is False. Automatic creation of intermediate directories when makeParents is True."""

	def doSvnOperation( self, *args ):
		# arguments
		urlOrPath = args[0]
		logMessage = args[1]
		if len(args)==3 and args[2]:
			makeParents = args[2]
		else:
			makeParents = True

		# do
		retVal = self.client.mkdir( urlOrPath, logMessage, makeParents )
		return retVal


class SvnRemove( SvnOperation ):
	"""SvnRemove()( urlOrPath, logMessage, [keepLocal]=True )
		If urlOrPath is an URL, the items are deleted from the repository via an immediate commit.
		If urlOrPath is a path, each item is scheduled for deletion upon the next commit. Files, and directories that have 
		not been committed, are immediately removed from the working copy. The command will not remove paths that are,
		or contain, unversioned or modified items.
		Set keepLocal to True to prevent the local file from being delete."""


	def doSvnOperation( self, *args ):
		# arguments
		urlOrPath = args[0]
		logMessage = args[1]
		if len(args)==3 and args[2]:
			keepLocal = args[2]
		else:
			keepLocal = True

		# do
		self.client.callback_get_log_message.message = logMessage
		retVal = self.client.remove( urlOrPath, keep_local=keepLocal )
		return retVal


# SvnCheckout, SvnExport, SvnUpdate, SvnCat
class SvnCheckout( SvnOperation ):
	"""SvnCheckout()( url, path, [revisionNumber] )
		Check out a working copy from a repository url into path to head or revisionNumber if provided
		@return revision number of the working copy"""

	def doSvnOperation( self, *args ):
		# arguments
		url = args[0]
		path = args[1]
		if len(args)==3 and args[2]:
			revision = pysvn.Revision( pysvn.opt_revision_kind.number, args[2] )
		else:
			revision = pysvn.Revision( pysvn.opt_revision_kind.head )

		# do
		#return self.client.checkout( url = url, path = path ) => returned revision contains always 0 !!!
		self.client.checkout( url = url, path = path, revision = revision )
		return SvnGetRevision()( path )


class SvnExport( SvnOperation ):
	"""SvnExport()( url, path, [revisionNumber] )
		Export a working copy from a repository url into path to head or revisionNumber if provided
		@return revision number of the exported copy"""

	def doSvnOperation( self, *args ):
		# arguments
		url = args[0]
		path = args[1]
		if len(args)==3 and args[2]:
			revision = pysvn.Revision( pysvn.opt_revision_kind.number, args[2] )
		else:
			revision = pysvn.Revision( pysvn.opt_revision_kind.head )

		# do
		rev = self.client.export( src_url_or_path = url, dest_path = path, revision = revision )
		return rev.number


class SvnUpdate( SvnOperation ):
	"""SvnUpdate()(path, [revisionNumber])
		Updates path to head or revisionNumber if provided
		@pre path must be a working copy of an svn repository
		@return revision number of the working copy"""

	def doSvnOperation( self, *args ):
		# argument(s)
		path = args[0]
		if len(args)==2 and args[1]:
			revision = pysvn.Revision( pysvn.opt_revision_kind.number, args[1] )
		else:
			revision = pysvn.Revision( pysvn.opt_revision_kind.head )

		# do
		revisionList = self.client.update( path, revision=revision )
		if len(revisionList)==1:
			revision = revisionList[0]
			if revision.kind == pysvn.opt_revision_kind.number:
				return revision.number
			else:
				raise AssertionError('revision.kind != pysvn.opt_revision_kind.number')
		else:
			raise AssertionError('len(revisionList)!=1')


class SvnCat( SvnOperation ):
	"""SvnCat()(urlOrPath, [revisionNumber])
		@brief Returns the content of urlOrPath for the specified revision if provided or head
		@return a string with the content of urlOrPath"""

	def __call__( self, urlOrPath, revisionNumber = None ):
		return SvnOperation.__call__(self, urlOrPath, revisionNumber)

	def doSvnOperation( self, *args ):
		# argument(s)
		urlOrPath = args[0]
		revision = args[1]

		if revision:
			revision = pysvn.Revision( pysvn.opt_revision_kind.number, revision )
		else:
			revision = pysvn.Revision( pysvn.opt_revision_kind.head )

		# do
		file_content = self.client.cat( urlOrPath, revision=revision )
		return file_content


# SvnRelocate
class SvnRelocate( SvnOperation ):
	"""SvnRelocate()(pathToWorkingCopy, toUrl, fromUrl) Relocates the working copy to toUrl.
		@pre pathToWorkingCopy	must be a working copy of an svn repository"""

	def doSvnOperation( self, *args ):
		# arguments
		pathToWorkingCopy = args[0]
		toUrl = args[1]
		fromUrl = args[2]

		# do
		self.client.relocate( fromUrl, toUrl, pathToWorkingCopy )


# SvnCopy
class SvnCopy( SvnOperation ):
	"""SvnCopy()( sourceUrlOrPath, sourceRevision, destinationUrlOrPath, logMessage, [makeParents]=True )
		Duplicate something in working copy or repository, remembering history
		@param makeParents	all the intermediate directories must already exist when makeParents is False. Automatic creation of intermediate directories when makeParents is True."""

	def doSvnOperation( self, *args ):
		# arguments
		sourceUrlOrPath = args[0]
		sourceRevision = args[1]
		destinationUrlOrPath = args[2]
		logMessage = args[3]
		if len(args)==5 and args[4]:
			makeParents = args[4]
		else:
			makeParents = True

		# do
		pySvnSourceRevision = pysvn.Revision( pysvn.opt_revision_kind.number, sourceRevision )
		self.setLogMessage( logMessage )
		retVal = self.client.copy2( [(sourceUrlOrPath, pySvnSourceRevision)], destinationUrlOrPath, make_parents=makeParents )
		return retVal


# @todo SvnStatus
class SvnStatus( SvnOperation ):
	"""SvnStatus()(path, getAll = True, checkRepository = False )
		@return  a list of PysvnStatus objects

		Returns the status of working copy files and directories"""

	def doSvnOperation( self, *args ):
		# argument
		path = args[0]
		getAll = args[1]

		# do
		return self.client.status( path )

# @todo SvnRemoteStatus



def atExitPrintStatistics( stats ):
	print
	stats.printReport()

class Subversion( IVersionControlSystem ):
	"""Subversion interface for sbf"""

	__mergeToolLaunchingPolicy	= None

	# Global statistics
	stats						= Statistics()

	# Merge
# @todo uses sbfUI
	def __getMergeToolLaunchingPolicy( self ):
		if self.__mergeToolLaunchingPolicy not in [ 'a', 'n' ] :
			# Asks user
			choice = raw_input("Select edit conflict policy:\n (a)lways, n(ever) or the default choice (o)nce ?")
			if choice not in [ 'a', 'n', 'o' ] :
				choice = 'o'
			# Saves choice
			self.__mergeToolLaunchingPolicy = choice

		return self.__mergeToolLaunchingPolicy

	def __mustLaunchMergeTool( self ):
		policy = self.__getMergeToolLaunchingPolicy()
		if policy == 'n':
			return False
		else:
			return True

	def __runConflictResolver( self, myProjectPathName, conflictedList ):
		"""Executes a conflict editor program on each element of conflictedList.
			@remark On Windows, TortoiseMerge is the default conflict editor."""

		if len(conflictedList) > 0 :
			print 'Launch conflict editor for:'
		else:
			return

		# Retrieves which merge tool to use
		mergeTool = None
		if sys.platform == 'win32':
			mergeTool = locateProgram( 'tortoisesvnmergecustom' )
			if not mergeTool:
				mergeTool = locateProgram('tortoisesvnmerge')
			#else nothing to do
			tortoiseMergeStyleParameters = (basename(mergeTool) == 'TortoiseMerge.exe')

		for (projectPathName, pathFilename) in conflictedList:
			print relpath(pathFilename, myProjectPathName)
			changes = SvnStatus()( pathFilename, True )
			for f in changes:
				dirPath	= dirname(f.path)
				new		= f.entry.conflict_new
				old		= f.entry.conflict_old
				work	= f.entry.conflict_work
				merged	= f.entry.name

				if self.__mustLaunchMergeTool() and mergeTool:
					if tortoiseMergeStyleParameters:
						#"C:\Program Files\TortoiseSVN\bin\TortoiseMerge.exe" /base:"E:\Dev\bin\currentProjects\default.options.r7684" /theirs:"E:\Dev\bin\currentProjects\default.options.r7841"
						# /mine:"E:\Dev\bin\currentProjects\default.options.mine" /merged:"E:\Dev\bin\currentProjects\default.options" /basename:"default.options.r7684"
						# /theirsname:"default.options.r7841" /minename:"default.options.mine" /mergedname:"default.options"
						# /groupuuid:"c59f667f6873f70ceadc69dd210ae58f" /saverequired
						cmd =	"@\"{exe}\" /base:\"{base}\" /theirs:\"{theirs}\" /mine:\"{mine}\" /merged:\"{merged}\"".format(
									exe		= mergeTool,
									base	= join( dirPath, old ),
									theirs	= join( dirPath, new ),
									mine	= join( dirPath, work ),
									merged	= join( dirPath, merged ) )
						cmd +=	" /basename:\"{basename}\" /theirsname:\"{theirsname}\" /minename:\"{minename}\" /mergedname:\"{mergedname}\" /saverequired".format(
							basename=old, theirsname=new, minename=work, mergedname=merged )
					else:
						# "C:\Program Files\Perforce\p4merge.exe" "E:\Dev\bin\currentProjects\default.options.r7684" "E:\Dev\bin\currentProjects\default.options.r7841"
						# "E:\Dev\bin\currentProjects\default.options.mine" "E:\Dev\bin\currentProjects\default.options"
						cmd =	"@\"{exe}\" \"{base}\" \"{mine}\" \"{theirs}\" \"{merged}\"".format(
									exe		= mergeTool,
									base	= join( dirPath, old ),
									mine	= join( dirPath, work ),
									theirs	= join( dirPath, new ),
									merged	= join( dirPath, merged ) )

					self.sbf.myEnv.Execute( cmd )
					print

	# SvnUrl
	def __searchSvnUrlList( self, projectName ):
		if projectName in self.mySvnUrls:
			return [self.mySvnUrls[projectName]]
		else:
			return self.mySvnUrls.get('', [])


	#
	def __printPySvnRevision( self, myProject, revision ):
		if revision.kind == pysvn.opt_revision_kind.number:
			printRevision( myProject, revision.number )
		else:
			raise AssertionError('revision.kind != pysvn.opt_revision_kind.number')

	def __printRevision( self, myProject, revisionList ):
		if isinstance(revisionList, list):
			if len(revisionList)==1:
				self.__printPySvnRevision( myProject, revisionList[0] )
			else:
				raise AssertionError('len(revision)!=1')
		else:
			self.__printPySvnRevision( myProject, revisionList )


	# @todo Migrates status to new api, then remove __printSvnInfo
	def __printSvnInfo( self, myProjectPathName, myProject ):
		revision = self.getRevision( myProjectPathName )
		if revision:
			print ("{0} at revision {1}".format(myProject, revision))
			return True
		else:
			# project probably not under svn
			print ("{0} not under svn".format(myProject))
			return False


	def __createPysvnClient__(self):
		client = pysvn.Client()
		client.callback_notify						= CallbackNotifyWrapper()
		client.callback_ssl_server_trust_prompt		= svnCallback_ssl_server_trust_prompt
		client.callback_get_login					= svnCallback_get_login
		client.exception_style						= 1
		return client

	def __init__( self, sbf = None, svnUrls = None ):
		# Prints global statistics at exit
		atexit.register( atExitPrintStatistics, self.stats )

		#
		self.sbf = sbf
		if sbf:
			self.mySvnUrls = sbf.myEnv['svnUrls']

		if svnUrls:
			self.mySvnUrls = svnUrls

		#
		self.client = self.__createPysvnClient__()


	### OPERATIONS ###
	def add( self, myProjectPathName, myProject ):
		"""@pre self.sbf != None"""

		# Tests if project is under vcs
		if svnIsUnversioned( myProjectPathName ):
			print ("Add the root directory of the project '{0}' under svn and relaunch this command.".format(myProject))
			return False

		# Retrieves all files for the project
		for file in self.sbf.getAllFiles(myProject):
			#
			pathfilename = join( myProjectPathName, file )
			path = dirname( pathfilename )

			#
			if svnIsUnversioned( pathfilename ):
				if svnIsUnversioned( path ):
					# Must add path under svn
					if SvnAddDirs(rootPath=myProjectPathName)( path, myProjectPathName ):
						# Must add file under svn now
						retVal = SvnAddFileOrDir(rootPath=myProjectPathName)( pathfilename )
						if not retVal: print('I\t{0}'.format( relpath(pathfilename, myProjectPathName) ))
					else:
						print('I\t{0}'.format( relpath(pathfilename, myProjectPathName) ))
				else:
					# Must add file under svn
					retVal = SvnAddFileOrDir(rootPath=myProjectPathName)( pathfilename )
					if not retVal: print('I\t{0}'.format( relpath(pathfilename, myProjectPathName) ))
			# else nothing to do
		return True


	def locateProject( self, projectName, verbose = False ):
		"""@return (url of repository containing the project 'projectName', revision) or None"""
		for svnUrl in self.__searchSvnUrlList( projectName ):
			(svnUrl, revision) = splitSvnUrl( svnUrl, projectName )
			if svnIsVersioned( svnUrl ):
				if verbose:	print ( "{project} found at {url}".format( project=projectName, url=svnUrl ) )
				return (svnUrl, revision)
			else:
				if verbose:	print ( "{project} not found at {url}".format( project=projectName, url=svnUrl ) )


	def _checkout( self, url, path, revision = None ):
		svnCheckout = SvnCheckout( rootPath=path, statisticsObservers=[self.stats] )
		if revision:
			revisionNumber = svnCheckout( url, path, revision ) 
		else:
			revisionNumber = svnCheckout( url, path ) 

		# Print revision and statistics
		printRevision( basename(path), revisionNumber )
		svnCheckout.printStatisticsReport()


	def checkout( self, myProjectPathName, myProject ):
		"""@pre self.mySvnUrls != None"""

		# Try a checkout
		for svnUrl in self.__searchSvnUrlList( myProject ):
			(svnUrl, revision) = splitSvnUrl( svnUrl, myProject )
			if SvnGetRevision()( svnUrl ):
				print ( "{project} found at {url}".format( project=myProject, url=svnUrl ) )
				self._checkout( svnUrl, myProjectPathName, revision )
				return True
			else:
				print ( "{project} not found at {url}".format( project=myProject, url=svnUrl ) )

		return False


	def _export( self, url, path, revision = None ):
		svnExport = SvnExport( rootPath=path, statisticsObservers=[self.stats] )
		if revision:
			revisionNumber = svnExport( url, path, revision ) 
		else:
			revisionNumber = svnExport( url, path ) 

		# Print revision and statistics
		printRevision( basename(path), revisionNumber )
		svnExport.printStatisticsReport()


# @todo migrate to new API SvnOperation
#	def export( self, myProjectPathName, myProject ):
#		# Checks validity of 'svnUrls' option
#		# @todo Checks if urls are valid
#		if len(self.sbf.mySvnUrls) == 0 :
#			raise SCons.Errors.UserError("Unable to do any svn export, because option 'svnUrls' is empty.")

#		# Try a export
#		client = self.__createPysvnClient__()
#		#client.callback_notify.resetStatistics()
#		svnUrls = self.__searchSvnUrlList( myProject )

#		for svnUrl in svnUrls :
#			# @todo improves robustness for svn urls
#			svnUrl = self.__completeUrl( svnUrl, myProject )
#			print "sbfInfo: Try to export a copy from", svnUrl, ":"
#			try :
#				revision = client.export( svnUrl, myProjectPathName )
#				#client.callback_notify.getStatistics().printReport()
#				print "sbfInfo:", myProject, "found at", svnUrl
#				return
#				#return self.__printSvnInfo( myProjectPathName, myProject )
#			except pysvn.ClientError, e :
#				print e.args[0], '\n'

#		return False


# @todo migrate to new API SvnOperation
#	def _export( self, svnUrl, exportPath, projectName ):
#		client = self.__createPysvnClient__()
#		#client.callback_notify.resetStatistics()
#		try:
#			revision = client.export( svnUrl, exportPath )
			#client.callback_notify.getStatistics().printReport()
#			print "sbfInfo:", projectName, "found at", svnUrl
#			return True
#			#return self.__printSvnInfo( exportPath, projectName )
#		except pysvn.ClientError, e :
#			print e.args[0], '\n'
#			return False


# @todo migrate to new API SvnOperation
	def clean( self, myProjectPathName, myProject ):
		# Tests if project is under vcs
		if svnIsUnversioned( myProjectPathName ):
			# @todo print message if verbose
			return

		try:
			client = self.__createPysvnClient__()
			client.cleanup( myProjectPathName )
			return True
		except pysvn.ClientError, e :
			print e.args[0], '\n'
			return False


	def relocate( self, myProjectPathName, myProject ):
		# Tests if project is under vcs
		if svnIsUnversioned( myProjectPathName ):
			# @todo print message if verbose
			return

		# Retrieves UUID and info of working copy
		workingUUID = SvnGetUUID()( myProjectPathName )
		workingInfo = SvnGetInfo()( myProjectPathName )

		# Tests if repository url of working copy is still valid
		for svnUrl in self.__searchSvnUrlList( myProject ):
			(svnUrl, revision) = splitSvnUrl( svnUrl, myProject )
			if SvnGetRevision()( svnUrl ):
				print ( "{project} working copy from {url}".format( project=myProject, url=workingInfo['URL'] ) )
				# Retrieves UUID and info of remote repository
				remoteUUID = SvnGetUUID()( svnUrl )
				remoteInfo = SvnGetInfo()( svnUrl )

				# Tests if a relocate is needed ?
				if (workingInfo['URL'] != remoteInfo['URL']) and\
				   (workingUUID == remoteUUID):
				   # urls: must do a relocate when urls are !=
				   # UUID: same UUID, so relocate operation is safe
					SvnRelocate()( myProjectPathName, remoteInfo['URL'], workingInfo['URL'] )
					print ( '{project} relocates to {svnUrl}'.format( project=myProject, svnUrl=remoteInfo['URL'] ) )
				return True
			# @todo in verbose mode
			#else:
			#	print ( "sbfInfo: {project} not found at {url}".format( project=myProject, url=svnUrl ) )

		return True


	def _update( self, path, revision ):
		project = basename(path)

		# Action
		svnUpdate = SvnUpdate( rootPath=path, statisticsObservers=[self.stats] )
		revisionNumber = svnUpdate( path, revision )

		# Print revision and statistics
		printRevision( project, revisionNumber )
		svnUpdate.printStatisticsReport()

		return svnUpdate.statistics


	def update( self, myProjectPathName, myProject ):
		# Tests if project is under vcs
		if svnIsUnversioned( myProjectPathName ):
			# @todo print message if verbose
			return

		# @todo OPTME if revision == head for WC (How to retrieve this info ?)
		# Gets WC informations
		infoWC = SvnGetInfo()( myProjectPathName )
		urlWC = infoWC['URL']
		revWC = infoWC['rev'].number
		#reposRootUrlWC = infoWC['repos_root_URL']

		# Search a matching urlWC in 'svnUrls' option
		for svnUrl in self.__searchSvnUrlList( myProject ):
			(url, rev) = splitSvnUrl( svnUrl, myProject )
			if ( url == urlWC ):
				break
		else:
			print ( "{project} working copy from {url}".format( project=myProject, url=urlWC ) )
			print ("sbfError: Unable to found a matching url in 'svnUrls' option of 'SConsBuildFramework.options'")
			print ("Execute the following command to resolve the problem: 'scons svnRelocate'.")
			exit(1)

		# Found a matching url
		if rev != revWC:
			# Do the update
			statistics = self._update( myProjectPathName, rev )

		# Run editor of conflict(s)
		self.__runConflictResolver( myProjectPathName, statistics.conflicted )

		return True


	def copy( self, sourcePath, destination, message ):
		"""	@param sourcePath	path to the current working copy used as the source for the copy (i.e. it defines repository url and revision, but WITHOUT any local modifications)
			@param destination	path in repository (i.e. '/tags/0.1' or '/branches/0.1')
			@param message		commit message

			@remark This is a complete server-side copy.
			"""

		#
		splittedUrlWC = self.getSplitUrl( sourcePath )

		#
		svnCopy = SvnCopy( rootPath = sourcePath, statisticsObservers=[self.stats] )

		# Gets WC informations
		reposUrlWC = splittedUrlWC[0]
		dirnameWC = splittedUrlWC[1]
		basenameWC = splittedUrlWC[2]
		revisionWC = splittedUrlWC[3]

		# Constructs destination url
		#print 'S:', reposUrlWC + dirnameWC + basenameWC + '@' + str(revisionWC)
		#print 'D:', reposUrlWC + dirnameWC + destination + '@' + str(revisionWC)
		#print message
		#print

		revisionNumber = svnCopy( reposUrlWC + dirnameWC + basenameWC, revisionWC, reposUrlWC + dirnameWC + destination, message )

		print message

		# Print revision and statistics
		self.__printRevision( basename(sourcePath), revisionNumber )
		svnCopy.printStatisticsReport()

		return revisionNumber

	def copy( self, project, sourceUrlOrPath, sourceRevision, destinationUrlOrPath, logMessage ):
		"""	@param project					name of project (used for output message)
			@param sourceUrlOrPath			
			@param sourceRevision			
			@param destinationUrlOrPath		
			@param logMessage				

			@remark see SvnCopy()"""

		#
		svnCopy = SvnCopy( rootPath = '', statisticsObservers=[self.stats] )

		revisionNumber = svnCopy( sourceUrlOrPath, sourceRevision, destinationUrlOrPath, logMessage )

		print logMessage

		# Print revision and statistics
		self.__printRevision( project, revisionNumber )
		svnCopy.printStatisticsReport()

		return revisionNumber


	def remove( self, pathToWC, branchToRemove, message ):
		"""	@param pathToWC			path to the current working copy used to define repository url, but WITHOUT any local modifications)
			@param branchToRemove	path in repository (i.e. '/tags/0.1' or '/branches/0.1')
			@param message			commit message

			@remark This is a complete server-side operation.
			"""

		#
		splittedUrlWC = self.getSplitUrl( pathToWC )

		#
		svnRemove = SvnRemove( rootPath = pathToWC, statisticsObservers=[self.stats] )

		# Gets WC informations
		reposUrlWC = splittedUrlWC[0]
		dirnameWC = splittedUrlWC[1]

		# Constructs url to remove
		revisionNumber = svnRemove( reposUrlWC + dirnameWC + branchToRemove, message )

		print message

		# Print revision and statistics
		self.__printRevision( basename(pathToWC), revisionNumber )
		svnRemove.printStatisticsReport()

		return revisionNumber


# @todo migrate to new API SvnOperation
	def status( self, myProjectPathName, myProject ):
		try:
			client = self.__createPysvnClient__()
			changes = client.status( myProjectPathName, get_all = False, update = True )

			normalStatus = [pysvn.wc_status_kind.normal, pysvn.wc_status_kind.none]

			localChanges	= [c for c in changes if c.text_status not in normalStatus and c.repos_text_status in normalStatus]
			repoChanges		= [c for c in changes if c.text_status in normalStatus and c.repos_text_status not in normalStatus]
			bothChanges		= [c for c in changes if (c.text_status not in normalStatus) and (c.repos_text_status not in normalStatus)]

			#stats = {}
			#stats['A']				= [f.path for f in changes if f.text_status == pysvn.wc_status_kind.added]
			#stats['removed']		= [f.path for f in changes if f.text_status == pysvn.wc_status_kind.deleted]
			#stats['changed']		= [f.path for f in changes if f.text_status == pysvn.wc_status_kind.modified]
			#stats['conflicts']		= [f.path for f in changes if f.text_status == pysvn.wc_status_kind.conflicted]
			#stats['unversioned']	= [f.path for f in changes if f.text_status == pysvn.wc_status_kind.unversioned]

			#stats['missing']		= [f.path for f in changes if f.text_status == pysvn.wc_status_kind.missing]
			#stats['merged']			= [f.path for f in changes if f.text_status == pysvn.wc_status_kind.merged]

			#stats['care']			= [f.path for f in changes if f.text_status not in normalStatus and f.repos_text_status not in normalStatus]
			#stats['r_modified']		= [f.path for f in changes if f.repos_text_status == pysvn.wc_status_kind.modified]
			#for f in changes:
			#	print f.path, f.text_status, f.repos_text_status
			dictStatus = {
				pysvn.wc_status_kind.added		: 'A',
				pysvn.wc_status_kind.conflicted	: 'C',
				pysvn.wc_status_kind.deleted	: 'D',
				pysvn.wc_status_kind.ignored	: 'I',
				pysvn.wc_status_kind.modified	: 'M',
				pysvn.wc_status_kind.replaced	: 'R',
				pysvn.wc_status_kind.external	: 'X',
				pysvn.wc_status_kind.unversioned: '?',
				}

			#client.callback_notify.resetStatistics()

			projectParentDirectory = dirname(myProjectPathName)

			if len(localChanges) > 0 :
				print ('only local modifications:')
				for c in localChanges:
					if c.text_status in dictStatus :
						text = dictStatus[c.text_status]
						#client.callback_notify.getStatistics().increments( text )
						self.stats.increments( text )
						print ('%s %s' % (text, convertPathAbsToRel(projectParentDirectory, c.path)) )
					else:
						print ('%s %s' % (c.text_status, convertPathAbsToRel(projectParentDirectory, c.path)) )
				print
			else:
				print ('no only local modifications')

			if len(repoChanges) > 0 :
				print ('only remote modifications:')
				for c in repoChanges:
					text = dictStatus[c.repos_text_status]
					#client.callback_notify.getStatistics().increments( text )
					self.stats.increments( text )
					if c.repos_text_status in dictStatus:
						print ('%s %s' % (text, convertPathAbsToRel(projectParentDirectory, c.path)) )
					else:
						print ('%s %s' % (c.repos_text_status, convertPathAbsToRel(projectParentDirectory, c.path)) )
				print
			else:
				print ('no only remote modifications')

			if len(bothChanges) > 0 :
				print ('local and remote modifications:')
				for c in bothChanges:
					text = dictStatus[c.text_status]
					repos_text = dictStatus[c.repos_text_status]
					#client.callback_notify.getStatistics().increments( text )
					#client.callback_notify.getStatistics().increments( repos_text )
					self.stats.increments( text )
					self.stats.increments( repos_text )
					if (c.text_status in dictStatus) and (c.repos_text_status in dictStatus) :
						print ('%s %s %s' % (text, repos_text, convertPathAbsToRel(projectParentDirectory, c.path)) )
					else:
						print ('%s %s %s' % (c.text_status, c.repos_text_status, convertPathAbsToRel(projectParentDirectory, c.path)) )
				print
			else:
				print ('no local and remote modifications')

			print
			#client.callback_notify.getStatistics().printReport()
#===============================================================================
#			for (k,v) in stats.iteritems():
#				if len(v) == 0:
#					continue
#				else:
#					for item in v :
#						print ('%s %s' % (k, convertPathAbsToRel( myProjectPathName, item ) ) )
#					print
#			for (k,v) in stats.iteritems():
#				if len(v) == 0:
#					continue
#				else:
#					print ( '%s:%i' % (k, len(v) ) ),
#					print
#===============================================================================
			return self.__printSvnInfo( myProjectPathName, myProject )
		except pysvn.ClientError, e :
			print e.args[0], '\n'
			return False


	def _listDir( self, urlOrPath, recurse = False, revisionNumber = None ):
		# Action
		svnListDirectory = SvnListDirectory( rootPath=urlOrPath, statisticsObservers=[self.stats] )
		if recurse:
			depth = pysvn.depth.infinity
		else:
			depth = pysvn.depth.immediates

		entries = svnListDirectory( urlOrPath, depth, revisionNumber=revisionNumber )
		return entries


	def listBranch( self, projectPathName, branch ):
		"""	@param projectPathName		the path of the project
			@param branch				'tags' or 'branches'
			@return a list containing all tag or branch available in repository for the given project
		"""
		# assert
		checkBranch( branch )

		url = self.getSplitUrl( projectPathName )
		urlBranch = url[0] + url[1] + '/{0}'.format(branch)
		if svnIsVersioned(urlBranch):
			return self._listDir( urlBranch, False )
		else:
			return []


# @todo migrate to new API SvnOperation
	def getAllVersionedFiles( self, myProjectPathName ):
		try:
			client = self.__createPysvnClient__()
			statusList = client.status( myProjectPathName )

			allFiles = [ status.path for status in statusList
							if status.is_versioned and
							(status.entry is not None and status.entry.kind == pysvn.node_kind.file) ]
			return allFiles
		except pysvn.ClientError, e :
			print e.args[0], '\n'
			return []


	def getUrl( self, urlOrPath ):
		"""@return svn url for the given 'urlOrPath' or None if not under vcs."""
		# Tests if project is under vcs
		if svnIsUnversioned( urlOrPath ):
			# @todo print message if verbose
			return

		# Gets WC informations
		infoWC = SvnGetInfo()( urlOrPath )
		return infoWC['URL']


	def getRevision( self, urlOrPath ):
		"""Returns the revision number for the given 'urlOrPath' or None if not under vcs"""
		revision = SvnGetRevision()(urlOrPath)
		return revision


	def getUrlAndRevision( self, urlOrPath ):
		"""@return (svn url, revision) for the given 'urlOrPath'."""
		# Tests if project is under vcs
		if svnIsUnversioned( urlOrPath ):
			# @todo print message if verbose
			return

		# Gets WC informations
		infoWC = SvnGetInfo()( urlOrPath )
		urlWC = infoWC['URL']
		revWC = infoWC['rev'].number
		return (urlWC, revWC)


	def getSplitUrl( self, urlOrPath ):
		"""Returns (reposUrl, dirname, basename, revision) or ('','','',0)
			example:
			 url												=> reposUrl								dirname		basename
			 http://project.googlecode.com/svn/foobar/trunk		=> http://project.googlecode.com/svn	/foobar		/trunk
			 http://project.googlecode.com/svn/foobar/tags/0.1	=> http://project.googlecode.com/svn	/foobar		/tags/0.1"""

		# Gets informations
		# @todo SvnGetRepositoryInfo()
		info = SvnGetInfo()( urlOrPath )
		if info == None:
			return ('','','',0)
		url = info['URL']
		reposUrl = info['repos_root_URL']
		rev = info['rev'].number

		dirnameBaseName = url.replace(reposUrl, '', 1)
		trunkLocation = dirnameBaseName.rfind( '/trunk' )
		tagsLocation = dirnameBaseName.rfind( '/tags' )
		branchesLocation = dirnameBaseName.rfind( '/branches' )
		if trunkLocation != -1:
			dirname = dirnameBaseName[:trunkLocation]
			basename = dirnameBaseName[trunkLocation:]
		elif tagsLocation != -1:
			dirname = dirnameBaseName[:tagsLocation]
			basename = dirnameBaseName[tagsLocation:]
		elif branchesLocation != -1:
			dirname = dirnameBaseName[:branchesLocation]
			basename = dirnameBaseName[branchesLocation:]
		else:
			print ('{0} must contain /trunk or /tags or /branches to be valid'.format(url))
			exit(1)

		return (reposUrl, dirname, basename, rev)


### Several helpers for url processing
def isUrl( urlOrPath ):
	return urlOrPath.find('://')>0

def urlJoin( path1, path2 ):
	if isUrl(path1):
		if path1[-1:] == '/':
			return path1 + path2
		else:
			return '{0}/{1}'.format(path1, path2)
	else:
		return join(path1,path2)


def anonymizeUrl( url ):
	"""Returns 'http://' instead of 'https://' or 'svn://' instead of 'svn+ssh://username@'"""
	# 'http://' instead of 'https://'
	url = url.replace('https://', 'http://', 1)
	# 'svn://' instead of 'svn+ssh://username@'
	reSvnSsh = re.compile('^svn\+ssh://.+@(.*)$')
	match = reSvnSsh.match(url)
	if match:
		url = 'svn://{0}'.format( match.group(1) )
	return url

def unanonymizeUrl( url ):
	"""Returns 'https://' instead of 'http://' or 'svn+ssh://' instead of 'svn://'"""
	# 'https://' instead of 'http://'
	url = url.replace('http://', 'https://', 1)
	# 'svn+ssh://' instead of 'svn://'
	url = url.replace('svn://', 'svn+ssh://', 1)
	return url


def removeTrunkOrTagsOrBranches( url ):
	"""Returns	'.../svn/projectName for '.../svn/projectName/trunk'
				'.../svn/projectName for '.../svn/projectName/tags/0.2'
				'.../svn/projectName for '.../svn/projectName/branches/2.0'"""
	# trunk
	index = url.rfind('/trunk')
	if index != -1:
		# Remove '/trunk...'
		return url[:index]

	# tags
	index = url.rfind('/tags')
	if index != -1:
		# Remove '/tags...'
		return url[:index]

	# branches
	index = url.rfind('/branches')
	if index != -1:
		# Remove '/branches...'
		return url[:index]

### Several helpers for branch management
def locateProject( vcs, projectName, verbose ):
	"""@return url of projectName (without trunk/tag/branch) or exit(1)"""
	projectLocation = vcs.locateProject( projectName, verbose )
	if projectLocation:
		projectSvnUrl = projectLocation[0]
		# Removes /trunk or /tags or /branches of projectSvnUrl
		projectSvnUrl = removeTrunkOrTagsOrBranches(projectSvnUrl)
		#if verbose: print ( "{project} found at {url}".format( project=projectName, url=projectSvnUrl ) )
		return projectSvnUrl
	else:
		print ( "Project '{project}' not found. Check your 'svnUrls' SConsBuildFramework option.".format( project=projectName ) )
		exit(1)


def checkBranch( branch ):
	if branch not in ['tags', 'branches']:
		raise AssertionError( "branch parameter must be 'tags' or 'branches'." )

def branch2branches( branch ):
	if branch == 'branch':
		return 'branches'
	else:
		assert( branch == 'tag' )
		return 'tags'

def branches2branch( branch ):
	if branch == 'branches':
		return 'branch'
	else:
		assert( branch == 'tags' )
		return 'tag'


# TAGS or BRANCHES
def localListSbfTagsOrBranches( path, tagsOrBranches, removeExtension = True ):
	"""	@param path				pathname of project where to search tags/branches files
		@param tagsOrBranches	choose what to search 'tags' or 'branches' files
		@param removeExtension	True to remove extension (i.e. '.tags' or 'branches') in the returning list
		@return a list containing all tags/branches available at 'path/branching', i.e. files matching path/branching/*.tags or *.branches."""
	assert( not isUrl(path) )

	branchingPath = join(path, 'branching')
	tags = [basename(elt) for elt in glob.iglob( '{}/*.{}'.format(branchingPath, tagsOrBranches) )]
	if removeExtension:
		tags = [ os.path.splitext(elt)[0] for elt in tags ]
	return tags

def remoteListSbfTagsOrBranches( urlOrPath, trunkOrBranches, tagsOrBranches, removeExtension = True ):
	"""	@param urlOrPath		path of the current working copy or url of the repository (without /trunk or /tags or /branches) where to search tags/branches files
		@param trunkOrBranches	'trunk' or 'branches/myBranch'
		@param tagsOrBranches	choose what to search 'tags' or 'branches' files
		@param removeExtension	True to remove extension (i.e. '.tags' or 'branches') in the returning list
		@return a list containing all tags/branches available at urlOrPath/branch location."""
	branchingUrlOrPath = urlJoin( urlOrPath, trunkOrBranches + '/branching' )
	if svnIsVersioned(branchingUrlOrPath):
		branches = SvnListFile()( branchingUrlOrPath, pysvn.depth.files, '*.{}'.format(tagsOrBranches) )
		if removeExtension:
			branches = [ os.path.splitext(elt)[0] for elt in branches ]
		return branches
	else:
		return []

def getLocalTagsOrBranchesContents( path, tagsOrBranches, desiredFile ):
	"""	@param path				pathname of project where to search 'tags' or 'branches' files
		@param tagsOrBranches	choose what to search 'tags' or 'branches' files
		@param desiredFile		name of the file containing tag/branch informations"""
	contents = ''
	with open( join(path, 'branching', desiredFile + '.' + tagsOrBranches) ) as file:
		contents = file.read()
	return contents

def remoteGetTagOrBranchesContents( urlOrPath, branch, tagsOrBranches, desiredFile ):
	"""	@param urlOrPath		path of the current working copy or url of the repository (without /trunk or /tags or /branches)
		@param branch			'trunk' or 'branches'
		@param tagsOrBranches	choose what to search 'tags' or 'branches' files
		@param desiredFile		name of the file containing tag/branch informations"""
	contents = SvnCat()( urlOrPath + '/' + branch + '/branching/' + desiredFile + '.' + tagsOrBranches )
	return contents

# TAGS
def localListSbfTags( path, removeExtension = True ):
	"""	@see localListSbfTagsOrBranches()"""
	return localListSbfTagsOrBranches(path, 'tags', removeExtension)

def remoteListSbfTags( urlOrPath, trunkOrBranches, removeExtension = True ):
	"""	@see remoteListSbfTagsOrBranches()"""
	return remoteListSbfTagsOrBranches( urlOrPath, trunkOrBranches, 'tags', removeExtension )

def getLocalTagsContents( path, desiredFile ):
	""" @see getLocalTagsOrBranchesContents()"""
	return getLocalTagsOrBranchesContents( path, 'tags', desiredFile )

def remoteGetTagContents( urlOrPath, branch, desiredFile ):
	return remoteGetTagOrBranchesContents( urlOrPath, branch, 'tags', desiredFile )

# BRANCHES
def localListSbfBranches( path, removeExtension = True ):
	"""	@see localListSbfTagsOrBranches()"""
	return localListSbfTagsOrBranches(path, 'branches', removeExtension)

def remoteListSbfBranches( urlOrPath, trunkOrBranches, removeExtension = True ):
	"""	@see remoteListSbfTagsOrBranches()"""
	return remoteListSbfTagsOrBranches( urlOrPath, trunkOrBranches, 'branches', removeExtension )

def getLocalBranchesContents( path, desiredFile ):
	""" @see getLocalTagsOrBranchesContents()"""
	return getLocalTagsOrBranchesContents( path, 'branches', desiredFile )

def remoteGetBranchesContents( urlOrPath, branch, desiredFile ):
	return remoteGetTagOrBranchesContents( urlOrPath, branch, 'branches', desiredFile )

#
def remoteListSvnBranches( urlOrPath, revisionNumber = None ):
	"""	@param urlOrPath		path of the current working copy or url of the repository (without /trunk or /tags or /branches)
		@param revisionNumber	None for head or a number for a specific revision (default value is None)
		@return a list containing all branches available at urlOrPath/branches location."""
	branchesUrlOrPath = urlJoin( urlOrPath, 'branches' )
	if svnIsVersioned(branchesUrlOrPath):
		branches = SvnListDirectory()( branchesUrlOrPath, pysvn.depth.immediates, revisionNumber=revisionNumber )
		return branches
	else:
		return []


# pretty print
def printSbfBranch( projectName, branch, branches, localPath ):
	"""	@param projectName		name of the project
		@param branch			'tags' or 'branches'
		@param branches			a list containing all tags or branches available
		@param localPath		True if branches have been retrieved from a local path (and not from a working copy or a repository)"""

	checkBranch(branch)

	if localPath:
		print ( "List of local {0} for project '{1}':".format(branch, projectName) )
	else:
		print ( "List of {0} for project '{1}':".format(branch, projectName) )
	if len(branches) > 0:
		for elt in branches:
			print (' - {0}'.format(elt))
	else:
		print ( ' * No {0}'.format(branch) )
	return branches
