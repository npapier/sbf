# SConsBuildFramework - Copyright (C) 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from src.sbfCygwin	import callCygpath2Unix
from src.sbfTools	import locateProgram

def __initializeEnvCygpath( lenv ):
	"""Initializes construction variable CYGPATH_LOCATION with path to cygpath executable."""
	cygpathLocation = locateProgram( 'cygpath' )
	if len(cygpathLocation)>0:
		lenv['CYGPATH_LOCATION'] = cygpathLocation
	#else nothing to do

def __initializeEnvSsh( lenv ):
	"""Initializes construction variable SSH_LOCATION with path to ssh executable."""
	sshLocation = locateProgram( 'ssh' )
	if len(sshLocation)>0:
		lenv['SSH_LOCATION'] = sshLocation
	#else nothing to do

def __initializeEnvRsync( lenv ):
	"""Initializes construction variables RSYNCFLAGS and RSYNCRSH.
	SSH_LOCATION and CYGPATH_LOCATION used internally are initialized too
	"""

	__initializeEnvCygpath(lenv)
	__initializeEnvSsh(lenv)

	# RSYNCFLAGS
	lenv['RSYNCFLAGS'] = "-av --chmod=u=rwX,go=rX" # --progress

	# RSYNCRSH
	if 'SSH_LOCATION' in lenv:
		sshLocation = lenv['SSH_LOCATION']
		if (lenv['PLATFORM'] == 'win32') and ('CYGPATH_LOCATION' in lenv):
			sshLocation = callCygpath2Unix( sshLocation, lenv['CYGPATH_LOCATION']).lower()
		lenv['RSYNCRSH'] = '--rsh={0}/ssh'.format( sshLocation )
	else:
		env['RSYNCRSH'] = ''



def createRsyncAction( lenv, target, source, alias = None, useDeleteOption = None ):
	"""if useDeleteOption is None, then weakPublishing option is used to choose if --delete option must be given to rsync or not.
	Sets useDeleteOption to override the weakPublishing option.
	Example of generated rsync command :
		rsync --delete -av --chmod=u=rwX,go=rX --rsh=/usr/bin/ssh /cygdrive/d/tmp/sbf/build/pak/ulisProduct_2-0-beta13_2012-02-01_setup.exe farmer@orange:/srv/files/Dev/buildbot/vista-farm/ulisProduct_2-0-beta13_2012-02-01_setup.exe
	"""

	if 'RSYNCFLAGS' not in lenv:
		__initializeEnvRsync(lenv)

	# source
	if len(lenv['CYGPATH_LOCATION'])>0:
		assert( lenv['PLATFORM']=='win32' )
		fullSource = callCygpath2Unix( source, lenv['CYGPATH_LOCATION'] )
	else:
		fullSource = source

	# destination
	publishPath = lenv['publishPath']
	publishPath = publishPath.rstrip('/')
	fullTarget = publishPath + '/' + str(target)

	# flags
	if useDeleteOption is None:
		if lenv.GetOption('weakPublishing'):
			dynamicFlags = ''
		else:
			dynamicFlags = '--delete'
	else:
		if useDeleteOption:
			dynamicFlags = '--delete'
		else:
			dynamicFlags = ''

	# cmd
	cmd = "rsync {rsyncFlags} {weakPublishingFlags} {rsh} '{src}' '{dst}'".format( rsyncFlags=lenv['RSYNCFLAGS'], weakPublishingFlags=dynamicFlags, rsh=lenv['RSYNCRSH'], src=fullSource, dst=fullTarget)

	rsyncAction = lenv.Command( '{0}_dummyRsync.out'.format(source), source, cmd )
	if alias:
		lenv.Alias( alias, rsyncAction )
	return rsyncAction
