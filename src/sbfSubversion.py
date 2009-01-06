# SConsBuildFramework - Copyright (C) 2005, 2007, 2008, 2009, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from sbfFiles import convertPathAbsToRel

##### Svn ######
def svnGetURLFromSBFOptions( sbf, projectName ):
	svnUrlsDict = sbf.myEnv['svnUrls']
	if projectName in svnUrlsDict :
		return [ svnUrlsDict[projectName] ]
	else:
		return svnUrlsDict['']

# Returns the url without modification if svnUrl ends with the '/trunk', otherwise returns the svnUrl with '/projectName/trunk' appended at the end.
# In all case, removes unneeded '/' at the end of the given svnUrl
def svnCompleteUrl( projectName, svnUrl ):
	if svnUrl.endswith( '/' ):
		svnUrl = svnUrl[:-1]

	if svnUrl.endswith( '/trunk' ):
		return svnUrl
	else:
		return svnUrl + '/' + projectName + '/trunk'

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
	import pysvn
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


def svnCallbackNotify( sbf, eventDict ) :
	import pysvn

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
		print wcNotifyActionMap[action], "\t",
		print convertPathAbsToRel( sbf.myProjectPathName, path )



class svnCallbackNotifyWrapper:
	def __init__( self, sbf ) :
		self.sbf	= sbf

	def __call__( self, eventDict ) :
		svnCallbackNotify( self.sbf, eventDict )



def svnCheckout( sbf ):
	# Checks validity of 'svnUrls' option
	# @todo Checks if urls are valid
	if len(sbf.mySvnUrls) == 0 :
		raise SCons.Errors.UserError("Unable to do any svn checkout, because option 'svnUrls' is empty.")

	# Try a checkout
	import pysvn
	client = pysvn.Client()
	client.callback_notify = svnCallbackNotifyWrapper( sbf )
	client.callback_ssl_server_trust_prompt	= svnCallback_ssl_server_trust_prompt
	client.callback_get_login				= svnCallback_get_login
	client.exception_style					= 0

	svnUrls = svnGetURLFromSBFOptions( sbf, sbf.myProject )

	for svnUrl in svnUrls :
		# @todo improves robustness for svn urls
		svnUrl = svnCompleteUrl( sbf.myProject, svnUrl )
		print "sbfInfo: Try to check out a working copy from", svnUrl, ":"
		try :
			revision = client.checkout(	url = svnUrl, path = sbf.myProjectPathName )
			print "sbfInfo:", sbf.myProject, "found at", svnUrl
			return printSvnInfo( sbf, client )
		except pysvn.ClientError, e :
			print str(e), "\n"

	return False



def svnUpdate( sbf ) :
	# Try an update
	import pysvn
	client = pysvn.Client()
	client.callback_notify = svnCallbackNotifyWrapper( sbf )
	client.callback_ssl_server_trust_prompt	= svnCallback_ssl_server_trust_prompt
	client.callback_get_login				= svnCallback_get_login
	client.exception_style					= 0

	try :
		revision = client.update( sbf.myProjectPathName )
		return printSvnInfo( sbf, client )
	except pysvn.ClientError, e :
		print str(e), "\n"
		return False
