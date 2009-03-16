# SConsBuildFramework - Copyright (C) 2005, 2007, 2008, 2009, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import os
import pysvn

from sbfFiles import convertPathAbsToRel



# Interface to version control system
class IVersionControlSystem :
	def __init__( self ):
		raise StandardError("IVersionControlSystem::__init__() not implemented")

	def checkout( self ):
		raise StandardError("IVersionControlSystem::checkout() not implemented")

	def update( self ):
		raise StandardError("IVersionControlSystem::update() not implemented")

	def status( self ):
		raise StandardError("IVersionControlSystem::status() not implemented")



##### Svn ######

def svnGetURL( path ) :
	import pysvn

	client = pysvn.Client()
	client.exception_style = 0

	try :
		info = client.info( path )
		if not info :
			return ""
		else :
			return info.url

	except pysvn.ClientError, e :
		print str(e)
		return ""

def svnGetAllVersionedFiles( path ) :

	import pysvn

	client = pysvn.Client()
	client.exception_style = 0

	try :
		statusList = client.status( path )

		allFiles = [ status.path for status in statusList
						if status.is_versioned and
						(status.entry is not None and status.entry.kind == pysvn.node_kind.file) ]

		return allFiles

	except pysvn.ClientError, e :
		print str(e)
		return []


def svnExport( sbf, project, destinationPath ) :
	# try an svn export
	import pysvn
	client = pysvn.Client()
	client.exception_style = 0

	for repository in sbf.mySvnUrls :
		svnUrl	= repository + project + '/trunk'		#@todo function to create svnUrl
		#svnUrl	= repository + '/' + sbf.myProject + '/trunk'
		print "sbfInfo: Try to export a working copy to ", destinationPath, " from", svnUrl, ":"
		try :
			revision	= client.export(	src_url_or_path = svnUrl,
											dest_path = destinationPath )
			print "sbfInfo:", project, "found at", svnUrl
			if ( revision.kind == pysvn.opt_revision_kind.number ) :
				print project, "at revision", revision.number
			else :
				print project, "at revision", revision.date
			return True
		except pysvn.ClientError, e :
			print str(e), "\n"
	else:
		return False

def svnExportAction( target, source, env ) :
	destinationPath	= str(target[0])
	project			= str(source[0])

	svnExport( env.sbf, project, destinationPath )


def printSvnInfo( sbf, client ) :
	entry = client.info( sbf.myProjectPathName )
	if not entry :
		# no entry (i.e. None and co), project probably not under svn
		return False
	if entry.revision.kind == pysvn.opt_revision_kind.number :
		print sbf.myProject, "at revision", entry.revision.number
	else :
		print sbf.myProject, "at revision", entry.revision.date
	return True



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



# @todo Moves into Subversion class
def svnCallbackNotify( self, statistics, eventDict ) :

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

	path = eventDict['path']
	if len(path) == 0 :
		# empty path, nothing to do
		return

	action = eventDict['action']

	if (wcNotifyActionMap.has_key(action) and (wcNotifyActionMap[action] is not None)						# known action that must trigger a message
	and not (action == pysvn.wc_notify_action.update_update and eventDict['kind'] == pysvn.node_kind.dir)	# but not in this special case
	):
		lookup = wcNotifyActionMap[action]
		contentState = eventDict['content_state']
		if contentState == pysvn.wc_notify_state.conflicted :
			self.conflicted.append( path )
			# Overridden wcNotifyActionMap[] result
			lookup = 'C'

		if lookup not in statistics :
			statistics[lookup] = 1
		else:
			statistics[lookup] += 1

		print lookup, "\t",
		print convertPathAbsToRel( self.sbf.myProjectPathName, path )



class svnCallbackNotifyWrapper:
	def __init__( self, sbf ) :
		self.sbf		= sbf

		self.statistics = {}
		self.conflicted = []

	def __call__( self, eventDict ) :
		svnCallbackNotify( self, self.statistics, eventDict )



#
# @todo svnCallbackNotifyWrapper
# svnCallback_ssl_server_trust_prompt
# svnCallback_get_login
class Subversion ( IVersionControlSystem ) :


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


	def __init__( self, sbf ):
		#
		self.sbf	= sbf

		#
		self.client = pysvn.Client()
		self.client.callback_notify						= svnCallbackNotifyWrapper( sbf )
		self.client.callback_ssl_server_trust_prompt	= svnCallback_ssl_server_trust_prompt
		self.client.callback_get_login					= svnCallback_get_login
		self.client.exception_style						= 0


	def checkout( self, myProjectPathName, myProject ):
		# Checks validity of 'svnUrls' option
		# @todo Checks if urls are valid
		if len(self.sbf.mySvnUrls) == 0 :
			raise SCons.Errors.UserError("Unable to do any svn checkout, because option 'svnUrls' is empty.")

		# Try a checkout
		svnUrls = self.__getURLFromSBFOptions( myProject )

		for svnUrl in svnUrls :
			# @todo improves robustness for svn urls
			svnUrl = self.__completeUrl( svnUrl, myProject )
			print "sbfInfo: Try to check out a working copy from", svnUrl, ":"
			try :
				revision = self.client.checkout( url = svnUrl, path = myProjectPathName )
				print "sbfInfo:", myProject, "found at", svnUrl
				return printSvnInfo( self.sbf, self.client )
			except pysvn.ClientError, e :
				print str(e), "\n"

		return False

	def update( self, myProjectPathName, myProject ) :
		try :
			revision = self.client.update( myProjectPathName )

	#		for (k,v) in self.client.callback_notify.statistics.iteritems():
	#			print ('%s:%i' %(k,v) ),
	#		if len(self.client.callback_notify.statistics) > 0 :
	#			print

			conflicted = self.client.callback_notify.conflicted
			if len(conflicted) > 0 :
				print
				print 'files with merge conflicts:'
				for f in conflicted:
					print convertPathAbsToRel( sbf.myProjectPathName, f )

#				for pathFilename in conflicted:
#					changes = client.status( pathFilename )
#					for f in changes:
#						dirPath	= os.path.dirname(f.path)
#						new		= f.entry.conflict_new
#						old		= f.entry.conflict_old
#						work	= f.entry.conflict_work

#						if sbf.myPlatform == 'win32':
#							sbf.myEnv.Execute(	'@TortoiseMerge %s %s %s' %
#												(os.path.join( dirPath, old), os.path.join( dirPath, work ), os.path.join( dirPath, new )) )
						#sbf.myEnv.Execute( 'TortoiseUDiff' )
			return printSvnInfo( self.sbf, self.client )
		except pysvn.ClientError, e :
			print str(e), "\n"
			return False

	def status( self, myProjectPathName, myProject ):
		try :
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

			if len(localChanges) > 0 :
				print ('only local modifications:')
				for c in localChanges:
					if c.text_status in dictStatus :
						print ('%s %s' % (dictStatus[c.text_status], convertPathAbsToRel(myProjectPathName, c.path)) )
					else:
						print ('%s %s' % (c.text_status, convertPathAbsToRel(myProjectPathName, c.path)) )
				print
			else:
				print ('no only local modifications')

			if len(repoChanges) > 0 :
				print ('only remote modifications:')
				for c in repoChanges:
					if c.repos_text_status in dictStatus :
						print ('%s %s' % (dictStatus[c.repos_text_status], convertPathAbsToRel(myProjectPathName, c.path)) )
					else:
						print ('%s %s' % (c.repos_text_status, convertPathAbsToRel(myProjectPathName, c.path)) )
				print
			else:
				print ('no only remote modifications')

			if len(bothChanges) > 0 :
				print ('local and remote modifications:')
				for c in bothChanges:
					if (c.text_status in dictStatus) and (c.repos_text_status in dictStatus) :
						print ('%s %s %s' % (dictStatus[c.text_status], dictStatus[c.repos_text_status], convertPathAbsToRel(myProjectPathName, c.path)) )
					else:
						print ('%s %s %s' % (c.text_status, c.repos_text_status, convertPathAbsToRel(myProjectPathName, c.path)) )
				print
			else:
				print ('no local and remote modifications')

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
			return printSvnInfo( self.sbf, self.client )
		except pysvn.ClientError, e :
			print str(e), "\n"
			return False


#===============================================================================
# def svnUpdate( sbf ) :
#	# Try an update
#	import pysvn
#	client = pysvn.Client()
#	client.callback_notify = svnCallbackNotifyWrapper( sbf )
#	client.callback_ssl_server_trust_prompt	= svnCallback_ssl_server_trust_prompt
#	client.callback_get_login				= svnCallback_get_login
#	client.exception_style					= 0
#
#	try :
# #
#		#changes = client.status( sbf.myProjectPathName )
#		#print 'files with merge conflicts:'
#		#print [f.path for f in changes if f.text_status == pysvn.wc_status_kind.conflicted]
# #		for f in changes:
# #			if f.text_status == pysvn.wc_status_kind.conflicted:
# #				print f
# #				print f.path
# #				print f.entry
# #				print f.text_status
# #				print
# #				print f.entry.commit_author
# #
# #
#		revision = client.update( sbf.myProjectPathName )
#
#		for (k,v) in client.callback_notify.statistics.iteritems():
#			print ('%s = %i' %(k,v) )
#
#		conflicted = client.callback_notify.conflicted
#		if len(conflicted) > 0 :
#			print
#			print 'files with merge conflicts:'
#			for f in conflicted:
#				print convertPathAbsToRel( sbf.myProjectPathName, f )
#			#print [f.path for f in changes if f.text_status == pysvn.wc_status_kind.conflicted]
#			#print conflicted
#
#			for pathFilename in conflicted:
#				changes = client.status( pathFilename )
#				for f in changes:
#					dirPath	= os.path.dirname(f.path)
#					new		= f.entry.conflict_new
#					old		= f.entry.conflict_old
#					work	= f.entry.conflict_work
#
#					if sbf.myPlatform == 'win32':
#						sbf.myEnv.Execute(	'@TortoiseMerge %s %s %s' %
#											(os.path.join( dirPath, old), os.path.join( dirPath, work ), os.path.join( dirPath, new )) )
#					#sbf.myEnv.Execute( 'TortoiseUDiff' )
#
#		return printSvnInfo( sbf, client )
#	except pysvn.ClientError, e :
#		print str(e), "\n"
#		return False
#===============================================================================
