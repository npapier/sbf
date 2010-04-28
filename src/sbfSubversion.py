# SConsBuildFramework - Copyright (C) 2005, 2007, 2008, 2009, 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import atexit
import os

try:
	import pysvn
except ImportError as e:
	print ('sbfWarning: pysvn is not installed.')
	raise e


from sbfIVersionControlSystem import IVersionControlSystem
from sbfFiles import convertPathAbsToRel


##### Svn ######

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


#===============================================================================
# def svnExport( sbf, project, destinationPath ) :
#	# try an svn export
#	import pysvn
#	client = pysvn.Client()
#	client.exception_style = 0
#
#	for repository in sbf.mySvnUrls :
#		svnUrl	= repository + project + '/trunk'		#@todo function to create svnUrl
#		#svnUrl	= repository + '/' + sbf.myProject + '/trunk'
#		print "sbfInfo: Try to export a working copy to ", destinationPath, " from", svnUrl, ":"
#		try :
#			revision	= client.export(	src_url_or_path = svnUrl,
#											dest_path = destinationPath )
#			print "sbfInfo:", project, "found at", svnUrl
#			if ( revision.kind == pysvn.opt_revision_kind.number ) :
#				print project, "at revision", revision.number
#			else :
#				print project, "at revision", revision.date
#			return True
#		except pysvn.ClientError, e :
#			print str(e), '\n'
#	else:
#		return False
#
# def svnExportAction( target, source, env ) :
#	destinationPath	= str(target[0])
#	project			= str(source[0])
#
#	svnExport( env.sbf, project, destinationPath )
#===============================================================================



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






class Statistics:

	def __init__( self ):
		self.reset()

	def reset( self ):
		self.details	= {}
		self.conflicted	= []
		self.merged		= []

	def increments( self, type ):
		if type not in self.details :
			self.details[type] = 1
		else:
			self.details[type] += 1

	def addConflicted( self, projectPathName, absPath ):
		self.conflicted.append( (projectPathName, absPath) )

	def addMerged( self, projectPathName, absPath ):
		self.merged.append( (projectPathName, absPath) )

	def printReport( self ):
		if len(self.details) + len(self.conflicted) + len(self.merged) > 0 :
			print 'svn report:'

		for (k,v) in self.details.iteritems():
			print ('%s:%i' %(k,v) ),
		if len(self.details) > 0 :
			print

		if len(self.conflicted) > 0:
			print 'conflicted:'
			for (projectPathname, pathFilename) in self.conflicted:
				print convertPathAbsToRel(projectPathname, pathFilename)
			print

		if len(self.merged) > 0:
			print 'merged:'
			for (projectPathname, pathFilename) in self.merged:
				print convertPathAbsToRel(projectPathname, pathFilename)



class CallbackNotifyWrapper:

	def __init__( self, sbf, subversion ):
		self.sbf		= sbf
		self.subversion	= subversion


	def resetStatistics( self ):
		self.stats = Statistics()

	def getStatistics( self ):
		return self.stats


	def __call__( self, eventDict ):
		self.__callbackNotify( eventDict )

	def __callbackNotify( self, eventDict ):
		path = eventDict['path']
		if len(path) == 0 :
			# empty path, nothing to do
			return

		action = eventDict['action']

		if (wcNotifyActionMap.has_key(action) and (wcNotifyActionMap[action] is not None)						# known action that must trigger a message
		and not (action == pysvn.wc_notify_action.update_update and eventDict['kind'] == pysvn.node_kind.dir)	# but not in this special case
		):
			lookupAction = wcNotifyActionMap[action]

			# Checks if there is a conflict
			contentState = eventDict['content_state']
			# @todo checks in depth wc_notify_state => M(erge)
			if contentState == pysvn.wc_notify_state.merged :
				lookupAction = 'G'
				self.stats.addMerged( self.sbf.myProjectPathName, path )
				self.subversion.stats.addMerged( self.sbf.myProjectPathName, path )
			elif contentState == pysvn.wc_notify_state.conflicted :
				# Overridden wcNotifyActionMap[] result
				lookupAction = 'C'
				self.stats.addConflicted( self.sbf.myProjectPathName, path )
				self.subversion.stats.addConflicted( self.sbf.myProjectPathName, path )

			# Updates statistics
			self.stats.increments( lookupAction )
			self.subversion.stats.increments( lookupAction )

			print lookupAction, "\t",
			if len(self.sbf.myProjectPathName)>0:
				print convertPathAbsToRel( self.sbf.myProjectPathName, path )
			else:
				print path


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
	def __printSvnInfo( self, myProjectPathName, myProject ):
#?
		entry = self.client.info( myProjectPathName )
		if not entry :
			# no entry (i.e. None and co), project probably not under svn
			return False
		if entry.revision.kind == pysvn.opt_revision_kind.number :
			print myProject, "at revision", entry.revision.number
		else :
			print myProject, "at revision", entry.revision.date
		return True


	def isVersioned( self, path ):
		try:
			info = self.client.info( path )
			if not info :
				return False
			else:
				return True
		except pysvn.ClientError, e :
			for message, code in e.args[1]:
				if code == 155007 :
					# Directory is not a working copy
					return False
			else:
				print e.args[0]
		return False


	def isUnversioned( self, path ):
		return not self.isVersioned( path )


	def getUrl( self, path ):
		try:
			info = self.client.info( path )
			if not info :
				return ""
			else:
				return info.url
		except pysvn.ClientError, e :
			print e.args[0]
			return ""

	#
	def __init__( self, sbf ):
		# Prints global statistics at exit
		atexit.register( atExitPrintStatistics, self.stats )

		#
		self.sbf	= sbf

		#
		self.client = pysvn.Client()
		self.client.callback_notify						= CallbackNotifyWrapper( sbf, self )
		self.client.callback_ssl_server_trust_prompt	= svnCallback_ssl_server_trust_prompt
		self.client.callback_get_login					= svnCallback_get_login
		self.client.exception_style						= 1


	def add( self, myProjectPathName, myProject ):
		# Tests if project is under vcs
		if self.isUnversioned( myProjectPathName ):
			return

		# Retrieves env for the incoming project
		lenv = self.sbf.getEnv( myProject )

		# Retrieves all files for the project
# @todo SConsBuildFramework::getAllFiles()
		projectFiles = lenv['sbf_include'] + lenv['sbf_src'] + lenv['sbf_share'] + lenv['sbf_rc'] + lenv['sbf_files']

		# @todo only one client.status() call for the project
		try:
			self.client.callback_notify.resetStatistics()
			for file in projectFiles:
				pathfilename = os.path.join(myProjectPathName, file)
				try:
					changes = self.client.status( file )
					if (len(changes) == 1) and (changes[0].text_status == pysvn.wc_status_kind.unversioned):
						# Adds a single file in a versioned directory
						self.client.add( pathfilename, recurse=False, ignore=True )
					# else nothing to do
				except pysvn.ClientError, e :
					for message, code in e.args[1]:
						if code in [155007, 720003]:
							# Directory is not under vcs

							# 155007: '' is not a working copy
							# 720003: @todo
						
							# Adds the directory containing the file to vcs
						# @todo this only works if the parent directory is already under vcs.
							self.client.add( os.path.dirname(pathfilename), ignore=True, depth=pysvn.depth.empty )
							# Adds a single file in a versioned directory
							self.client.add( pathfilename, recurse=False, ignore=True )
						else:
							#print 'Code:',code,'Message:',message
							print e.args[0]
			self.client.callback_notify.getStatistics().printReport()
			return True
		except pysvn.ClientError, e :
			print e.args[0], '\n'
			return False


	def checkout( self, myProjectPathName, myProject ):
		# Checks validity of 'svnUrls' option
		# @todo Checks if urls are valid
		if len(self.sbf.mySvnUrls) == 0 :
			raise SCons.Errors.UserError("Unable to do any svn checkout, because option 'svnUrls' is empty.")

		# Try a checkout
		self.client.callback_notify.resetStatistics()
		svnUrls = self.__getURLFromSBFOptions( myProject )

		for svnUrl in svnUrls :
			# @todo improves robustness for svn urls
			svnUrl = self.__completeUrl( svnUrl, myProject )
			print "sbfInfo: Try to check out a working copy from", svnUrl, ":"
			try :
				revision = self.client.checkout( url = svnUrl, path = myProjectPathName )
				self.client.callback_notify.getStatistics().printReport()
				print "sbfInfo:", myProject, "found at", svnUrl
				return self.__printSvnInfo( myProjectPathName, myProject )
			except pysvn.ClientError, e :
				print e.args[0], '\n'

		return False


	def clean( self, myProjectPathName, myProject ):
		# Tests if project is under vcs
		if self.isUnversioned( myProjectPathName ):
			return

		try:
			self.client.cleanup( myProjectPathName )
			return True
		except pysvn.ClientError, e :
			print e.args[0], '\n'
			return False


	# @todo switch update <-> status
	def update( self, myProjectPathName, myProject ):
		# Tests if project is under vcs
		if self.isUnversioned( myProjectPathName ):
			return

		try:
			self.client.callback_notify.resetStatistics()

			#self.stats.clear()
			#self.client.callback_notify.conflicted = []

			revision = self.client.update( myProjectPathName )

			self.client.callback_notify.getStatistics().printReport()
	#		self.stats.printReport()

			conflicted = self.client.callback_notify.getStatistics().conflicted
			if len(conflicted) > 0 :
	#			print
	#			print 'files with merge conflicts:'
	#			for f in conflicted:
	#				print convertPathAbsToRel( myProjectPathName, f )

				for (projectPathname, pathFilename) in conflicted:
					changes = self.client.status( pathFilename )
					for f in changes:
						dirPath	= os.path.dirname(f.path)
						new		= f.entry.conflict_new
						old		= f.entry.conflict_old
						work	= f.entry.conflict_work
						merged	= f.entry.name

						if self.sbf.myPlatform == 'win32':
							if self.__mustLaunchMergeTool():
								# @todo WhereIs( TortoiseMerge ) to check availibility (here and in sbfCheck too)
								# @todo Tests if TortoiseMerge is available
								# @todo TortoiseUDiff ?
								cmd =	"@TortoiseMerge.exe /base:\"%s\" /theirs:\"%s\" /mine:\"%s\" /merged:\"%s\"" % (
											os.path.join( dirPath, old ),
											os.path.join( dirPath, new ),
											os.path.join( dirPath, work ),
											os.path.join( dirPath, merged ) )
								cmd +=	"/basename:\"%s\" /theirsname:\"%s\" /minename:\"%s\" /mergedname:\"%s\"" % ( old, new, work, merged )
								self.sbf.myEnv.Execute( cmd )

			return self.__printSvnInfo( myProjectPathName, myProject )

		except pysvn.ClientError, e :
			print e.args[0], '\n'
			return False


	def status( self, myProjectPathName, myProject ):
		try:
			changes = self.client.status( myProjectPathName, get_all = False, update = True )

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

			self.client.callback_notify.resetStatistics()

			projectParentDirectory = os.path.dirname(myProjectPathName)

			if len(localChanges) > 0 :
				print ('only local modifications:')
				for c in localChanges:
					if c.text_status in dictStatus :
						text = dictStatus[c.text_status]
						self.client.callback_notify.getStatistics().increments( text )
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
					self.client.callback_notify.getStatistics().increments( text )
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
					self.client.callback_notify.getStatistics().increments( text )
					self.client.callback_notify.getStatistics().increments( repos_text )
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
			self.client.callback_notify.getStatistics().printReport()
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
			statusList = self.client.status( myProjectPathName )

			allFiles = [ status.path for status in statusList
							if status.is_versioned and
							(status.entry is not None and status.entry.kind == pysvn.node_kind.file) ]
			return allFiles
		except pysvn.ClientError, e :
			print e.args[0], '\n'
			return []
