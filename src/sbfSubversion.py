# SConsBuildFramework - Copyright (C) 2005, 2007, 2008, 2009, 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import atexit
import fnmatch

try:
	import pysvn
except ImportError as e:
	print ('sbfWarning: pysvn is not installed.')
	raise e

from os.path import basename, dirname, isfile, isdir, join, normpath, relpath
from sbfIVersionControlSystem import IVersionControlSystem
from sbfFiles import convertPathAbsToRel # @todo replaces by relpath
from SCons.Script import *

# RUN @todo removes all self.sbf
# @todo svnUpdate/checkout@revisionNumber
# @todo svnTag, svnBranch => svn copy
# @todo svnSwitch => svn switch
# @todo svnRelocate => svn switch --relocate
# svn info => SvnGetUUID and co
# svnLogIncoming
# @todo a global atexit (see SCons ?)
# checkout, cleanup, export
# commit, merge, mergeinfo


### Statistics ###
class Statistics:
	def __init__( self ):
		self.reset()

	def reset( self ):
		# dict[type] = count
		self.details	= {}
		#
		self.conflicted	= []
		self.merged		= []

	def increments( self, type ):
		self.details[type] = self.details.get(type, 0) + 1

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


def svnCallback_get_login( realm, username, may_save ):
	print ('Authentication realm: %s' % realm)

	givenUsername = raw_input('Username (%s):' % username)
	if len(givenUsername) == 0:
		givenUsername = username

	givenPassword = raw_input("Password for '%s':" % givenUsername)

	return (len(givenUsername) != 0) and (len(givenPassword) != 0), givenUsername, givenPassword, may_save


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

		if (action in self.wcNotifyActionMap and (self.wcNotifyActionMap[action] is not None)								# known action that must trigger a message
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

			print lookupAction, "\t",
			if len(self.rootPath) > 0:
				print convertPathAbsToRel( self.rootPath, path ) # @todo os.path.relpath() ?
			else:
				print path



class SvnOperation:
	"""Encapsulation of svn operation(s) using pysvn."""

	# @todo OPTME adds a client parameter __init__()
	def __init__( self, rootPath = '', statisticsObservers = [] ):
		# Creates and configures pysvn client
		client = pysvn.Client()
		client.callback_notify						= CallbackNotifyWrapper( rootPath, statisticsObservers )
		client.callback_ssl_server_trust_prompt		= svnCallback_ssl_server_trust_prompt
		client.callback_get_login					= svnCallback_get_login
		client.exception_style						= 1

		self.client = client

		# Creates my own instance of Statistics and attaches to client
		self.statistics = Statistics()

	def __call__( self, *args ):
		try:
			self.client.callback_notify.attach( self.statistics )		
			retVal = self.doSvnOperation( *args )
			self.client.callback_notify.detach( self.statistics )
			return retVal
		except pysvn.ClientError as e:
			print ('{0}\n'.format(e.args[0]))
			#print e.args[1]
			raise SCons.Errors.StopError('An error occurs during an svn operation.')

	def doSvnOperation( self, *args ):
		raise AssertionError( '{0}::doSvnOperation() not implemented.'.format(self) )

	def printStatisticsReport( self ):
		self.statistics.printReport()


class SvnGetInfo( SvnOperation ):
	"""SvnGetInfo()(url_or_path)
		@param url_or_path
		@return None if not under vcs, otherwise returns the desired info"""

	def doSvnOperation( self, *args ):
		# argument
		url_or_path = args[0]

		# do
		try:
			entry_list = self.client.info2( url_or_path, depth = pysvn.depth.empty )
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
				if errorCode in [155007, 170000, 200005]:
					# 155007 : "'path' is not a working copy"
					# 170000 : "URL 'url' non-existent in revision REVNUM
					# 200005 : "'path' is not under version control"
					return
				else:
					raise e
			else:
				raise AssertionError('len(pysvn.ClientError)!=1')

class SvnGetRevision( SvnGetInfo ):
	"""SvnGetRevision()(url_or_path)
		@param url_or_path
		@return None if not under vcs, otherwise returns the revision number"""

	def doSvnOperation( self, *args ):
		retVal = SvnGetInfo.doSvnOperation( self, *args )
		if retVal:
			return retVal['rev'].number


class SvnGetUUID( SvnGetInfo ):
	"""SvnGetUUID()(url_or_path)
		@param url_or_path
		@return None if not under vcs, otherwise returns the repository UUID"""

	def doSvnOperation( self, *args ):
		retVal = SvnGetInfo.doSvnOperation( self, *args )
		if retVal:
			return retVal['repos_UUID']


class SvnGetLocalAndRemoteRevision( SvnGetInfo ):
	"""SvnGetLocalAndRemoteRevision()( workingCopyPath )
		@param workingCopyPath	path to the current working copy
		@return None if not under vcs, otherwise returns (localRevisionNumber, remoteRevisionNumber)"""

	def doSvnOperation( self, *args ):
		workingInfo = SvnGetInfo.doSvnOperation( self, *args )
		if workingInfo:
			remoteInfo = SvnGetInfo.doSvnOperation( self, workingInfo['URL'] )
			if remoteInfo:
				return (workingInfo['rev'].number, remoteInfo['rev'].number)


class SvnUpdateAvailable( SvnGetLocalAndRemoteRevision ):
	"""SvnUpdateAvailable()( workingCopyPath )
		@param workingCopyPath	path to the current working copy
		@return None if not under vcs, otherwise returns True if there is an update available, Falise if not"""

	def doSvnOperation( self, *args ):
		retVal = SvnGetLocalAndRemoteRevision.doSvnOperation( self, *args )
		if retVal:
			workingRev = retVal[0];
			remoteRev = retVal[1]
			return workingRev < remoteRev


def svnIsUnversioned( path ):
	revision = SvnGetRevision()(path)
	return revision == None


def svnIsVersioned( path ):
	return not SvnIsUnversioned(path)


#@todo pysvn seems to be unaware of svn:ignore properties. pysvn bug or wrong pysvn usage ?
class SvnAddFileOrDir( SvnOperation ):
	"""	SvnAddFileOrDir()(path)
		@pre dirname(path) must be under svn"""

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
				if not SvnAddFileOrDir()( currentPath ):
					return False
			#else nothing to do
		return True


class SvnCheckout( SvnOperation ):
	"""SvnCheckout()( url, path ) Check out a working copy from a repository url into path
		@return revision number of the working copy"""

	def doSvnOperation( self, *args ):
		# argument
		url = args[0]
		path = args[1]

		# do
		#return self.client.checkout( url = url, path = path ) => returned revision contains always 0 !!!
		self.client.checkout( url = url, path = path )
		return SvnGetRevision()( path )
# @todo @revision


class SvnRelocate( SvnOperation ):
	"""SvnRelocate()(pathToWorkingCopy, toUrl, fromUrl) Relocates the working copy to toUrl.
		@pre pathToWorkingCopy	must be a working copy of an svn repository"""

	def doSvnOperation( self, *args ):
		# argument
		pathToWorkingCopy = args[0]
		toUrl = args[1]
		fromUrl = args[2]

		# do
		self.client.relocate( fromUrl, toUrl, pathToWorkingCopy )


class SvnUpdate( SvnOperation ):
	"""SvnUpdate()(path) Updates path
		@pre path must be a working copy of an svn repository
		@return revision number of the working copy"""		

	def doSvnOperation( self, *args ):
		# argument
		path = args[0]

		# do
		revisionList = self.client.update( path )
		if len(revisionList)==1:
			revision = revisionList[0]
			if revision.kind == pysvn.opt_revision_kind.number:
				return revision.number
			else:
				raise AssertionError('revision.kind != pysvn.opt_revision_kind.number')
		else:
			raise AssertionError('len(revisionList)!=1')


class SvnStatus( SvnOperation ):
	"""SvnStatus()(path) Returns the status of working copy files and directories
		@return  a list of PysvnStatus objects"""

	def doSvnOperation( self, *args ):
		# argument
		path = args[0]

		# do
		return self.client.status( path )


def atExitPrintStatistics( stats ):
	print
	stats.printReport()

# @todo isBuildNeeded() => buildbot
# Usage without sbf
# create/applyPatch
# svnCallback_ssl_server_trust_prompt
# svnCallback_get_login
class Subversion ( IVersionControlSystem ) :

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
			@pre self.sbf != 0
			@remark On windows, TortoiseMerge is the default conflict editor."""

		if len(conflictedList) > 0 :
			print 'Launch conflict editor for:'

		for (projectPathName, pathFilename) in conflictedList:
			print relpath(pathFilename, myProjectPathName)
			changes = SvnStatus()( pathFilename )
			for f in changes:
				dirPath	= dirname(f.path)
				new		= f.entry.conflict_new
				old		= f.entry.conflict_old
				work	= f.entry.conflict_work
				merged	= f.entry.name

				if self.sbf.myPlatform == 'win32':
					if self.__mustLaunchMergeTool():
						# @todo Tests if TortoiseMerge is available
						cmd =	"@TortoiseMerge.exe /base:\"%s\" /theirs:\"%s\" /mine:\"%s\" /merged:\"%s\"" % (
									join( dirPath, old ),
									join( dirPath, new ),
									join( dirPath, work ),
									join( dirPath, merged ) )
						cmd +=	"/basename:\"%s\" /theirsname:\"%s\" /minename:\"%s\" /mergedname:\"%s\"" % ( old, new, work, merged )
						self.sbf.myEnv.Execute( cmd )
						print

	# URL
	def __getURLFromSBFOptions( self, projectName ):
		svnUrlsDict = self.sbf.myEnv['svnUrls']
		if projectName in svnUrlsDict :
			return [ svnUrlsDict[projectName] ]
		else:
			return svnUrlsDict['']

	# Returns the url without modification if svnUrl ends with the '/trunk', otherwise returns the svnUrl with '/projectName/trunk' appended at the end.
	# In all case, removes unneeded '/' at the end of the given svnUrl
	def __completeUrl( self, svnUrl, projectName ):
		if svnUrl.endswith( '/' ):
			svnUrl = svnUrl[:-1]

		if svnUrl.endswith( '/trunk' ):
			return svnUrl
		else:
			return svnUrl + '/' + projectName + '/trunk'


	#
	def __printPySvnRevision( self, myProject, revision ):
		if revision.kind == pysvn.opt_revision_kind.number:
			print ("{0} at revision {1}".format(myProject, revision.number))
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


	def __printRevision( self, myProject, revisionNumber ):
		print ("{0} at revision {1}".format(myProject, revisionNumber))

	# @todo remove
	def __printSvnInfo( self, myProjectPathName, myProject ):
		revision = self.getRevision( myProjectPathName )
		if revision:
			print ("{0} at revision {1}".format(myProject, revision))
			return True
		else:
			# project probably not under svn
			print ("{0} not under svn".format(myProject))
			return False


	def isVersioned( self, path ):
		return self.getRevision(path) != None

	def isUnversioned( self, path ):
		return not self.isVersioned( path )


	def getRevision( self, path ):
		"""Returns None if not under vcs, otherwise returns the revision number"""
		try:
# [TEST] @todo Don't share pysvn client instance (see below).
			client = self.__createPysvnClient__()
			entry_list = client.info2( path, depth = pysvn.depth.empty )
			if len(entry_list)==0:
				return
			else:
				infoDict = entry_list[0][1]
#				print fmtDateTime(infoDict['last_changed_date'])
				return infoDict['rev'].number
		except pysvn.ClientError as e :
#			if isinstance(e, tuple):
			for message, code in e.args[1]:
				print 'AAAA'
				print code
				if code in [155007, 200005]:
					# Directory is not a working copy
					return
			else:
				print e.args[0]
#			else:
#				print type(e)
#				print ('In project {0}, error {1}'.format(path, e))
		return


	def getUrl( self, path ):
		try:
			client = self.__createPysvnClient__()
			info = client.info( path )
			if not info :
				return ""
			else:
				return info.url
		except pysvn.ClientError, e :
			print e.args[0]
			return ""

	#
	def __createPysvnClient__(self):
		client = pysvn.Client()
		client.callback_notify						= CallbackNotifyWrapper()
		client.callback_ssl_server_trust_prompt		= svnCallback_ssl_server_trust_prompt
		client.callback_get_login					= svnCallback_get_login
		client.exception_style						= 1
		return client

	def __init__( self, sbf = None ):
# @todo global exit for sbf
		# Prints global statistics at exit
		atexit.register( atExitPrintStatistics, self.stats )

# @todo remove me ?
		#
		self.sbf = sbf

		#
		self.client = self.__createPysvnClient__()


	def add( self, myProjectPathName, myProject ):
		"""@pre self.sbf != None"""

		# Tests if project is under vcs
		if svnIsUnversioned(myProjectPathName):
			print ("Add the root directory of the project '{0}' under svn and relaunch this command.".format(myProject))
			return False

		# Retrieves all files for the project
		for file in self.sbf.getAllFiles(myProject):
			#
			pathfilename = join(myProjectPathName, file)
			path = dirname(pathfilename)

			#
			if svnIsUnversioned( pathfilename ):
				if svnIsUnversioned( path ):
					# Must add path under svn
					if SvnAddDirs()( path, myProjectPathName ):
						# Must add file under svn now
						retVal = SvnAddFileOrDir()( pathfilename )
						if not retVal: print('I\t{0}'.format( relpath(pathfilename, myProjectPathName) ))
					else:
						print('I\t{0}'.format( relpath(pathfilename, myProjectPathName) ))
				else:
					# Must add file under svn
					retVal = SvnAddFileOrDir()( pathfilename )
					if not retVal: print('I\t{0}'.format( relpath(pathfilename, myProjectPathName) ))
			# else nothing to do
		return True


	def checkout( self, myProjectPathName, myProject ):
		"""@pre self.sbf != None => mySvnUrls"""

		# Try a checkout
		for svnUrl in self.__getURLFromSBFOptions( myProject ):
			# @todo improves robustness for svn urls
			svnUrl = self.__completeUrl( svnUrl, myProject )
			if SvnGetRevision()( svnUrl ):
				print ( "{project} found at {url}".format( project=myProject, url=svnUrl ) )
				svnCheckout = SvnCheckout( rootPath=myProjectPathName, statisticsObservers=[self.stats] )
				revisionNumber = svnCheckout( svnUrl, myProjectPathName ) 

				# Print revision and statistics
				self.__printRevision( myProject, revisionNumber )
				svnCheckout.printStatisticsReport()
				return True
			else:
				print ( "{project} not found at {url}".format( project=myProject, url=svnUrl ) )

		return False


	def export( self, myProjectPathName, myProject ):
		# Checks validity of 'svnUrls' option
		# @todo Checks if urls are valid
		if len(self.sbf.mySvnUrls) == 0 :
			raise SCons.Errors.UserError("Unable to do any svn export, because option 'svnUrls' is empty.")

		# Try a export
		client = self.__createPysvnClient__()
		#client.callback_notify.resetStatistics()
		svnUrls = self.__getURLFromSBFOptions( myProject )

		for svnUrl in svnUrls :
			# @todo improves robustness for svn urls
			svnUrl = self.__completeUrl( svnUrl, myProject )
			print "sbfInfo: Try to export a copy from", svnUrl, ":"
			try :
				revision = client.export( svnUrl, myProjectPathName )
				#client.callback_notify.getStatistics().printReport()
				print "sbfInfo:", myProject, "found at", svnUrl
				return
				#return self.__printSvnInfo( myProjectPathName, myProject )
			except pysvn.ClientError, e :
				print e.args[0], '\n'

		return False


	def export( self, svnUrl, exportPath, projectName ):
		client = self.__createPysvnClient__()
		#client.callback_notify.resetStatistics()
		try:
			revision = client.export( svnUrl, exportPath )
			#client.callback_notify.getStatistics().printReport()
			print "sbfInfo:", projectName, "found at", svnUrl
			return True
			#return self.__printSvnInfo( exportPath, projectName )
		except pysvn.ClientError, e :
			print e.args[0], '\n'
			return False


	def clean( self, myProjectPathName, myProject ):
		# Tests if project is under vcs
		if self.isUnversioned( myProjectPathName ):
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
		for svnUrl in self.__getURLFromSBFOptions( myProject ):
			# @todo improves robustness for svn urls
			svnUrl = self.__completeUrl( svnUrl, myProject )
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


	# @todo switch update <-> status
	def update( self, myProjectPathName, myProject ):
		# Tests if project is under vcs
		if svnIsUnversioned( myProjectPathName ):
			# @todo print message if verbose
			return

		# Do the update
		svnUpdate = SvnUpdate( rootPath=myProjectPathName, statisticsObservers=[self.stats] )
		revisionNumber = svnUpdate( myProjectPathName )

		# Print revision and statistics
		self.__printRevision( myProject, revisionNumber )
		svnUpdate.printStatisticsReport()

		# Run editor of conflict(s)
		self.__runConflictResolver( myProjectPathName, svnUpdate.statistics.conflicted )

		return True



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


	#
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

#def fmtDateTime( t ):
#	import time
#	return time.strftime( '%d-%b-%Y %H:%M:%S', time.localtime( t ) )

