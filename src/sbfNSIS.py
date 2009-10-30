# SConsBuildFramework - Copyright (C) 2009, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from __future__ import with_statement

from SCons.Script import *

from src.sbfFiles	import *
from src.sbfUses import UseRepository
from src.SConsBuildFramework import stringFormatter, SConsBuildFramework, nopAction

def nsisGeneration( target, source, env ):

	# Retrieves/computes additional information
	targetName = str(target[0])

	# Open output file
	with open( targetName, 'w' ) as file:
		# Retrieves informations (all executables, ...)
		products	= []
		executables	= []
		for projectName in env.sbf.myParsedProjects :
			lenv = env.sbf.myParsedProjects[projectName]
			if lenv['type'] == 'exec' :
				print lenv['sbf_project'], os.path.basename(lenv['sbf_bin'][0])
				products.append( lenv['sbf_project'] )
				executables.append( os.path.basename(lenv['sbf_bin'][0]) )

		# Generates PRODUCTNAME
		PRODUCTNAME = ''
		for (i, product) in enumerate(products) :
			PRODUCTNAME += "!define PRODUCTNAME%s	\"%s\"\n" % (i, product)
		PRODUCTNAME += "!define PRODUCTNAME	${PRODUCTNAME0}\n"

		# Generates PRODUCTEXE, SHORTCUT and UNINSTALL_SHORTCUT
		PRODUCTEXE	= ''
		if len(executables) > 1 :
			SHORTCUT = '  CreateDirectory \"$SMPROGRAMS\\${PRODUCTNAME}\\tools\"\n'
			UNINSTALL_SHORTCUT	=	'  Delete "$SMPROGRAMS\\${PRODUCTNAME}\\tools\\*.*\"\n'
			UNINSTALL_SHORTCUT	+=	'  RMDir "$SMPROGRAMS\\${PRODUCTNAME}\\tools\"\n'
		else:
			SHORTCUT			= ''
			UNINSTALL_SHORTCUT	= ''

		for (i, executable) in enumerate(executables) :
			PRODUCTEXE	+=	"!define PRODUCTEXE%s	\"%s\"\n" % (i, executable)
			if i > 0 :
				SHORTCUT	+=	"  CreateShortCut \"$SMPROGRAMS\\${PRODUCTNAME}\\tools\\${PRODUCTNAME%s}.lnk\" \"$INSTDIR\\bin\\${PRODUCTEXE%s}\" \"\" \"$INSTDIR\\bin\\${PRODUCTEXE%s}\" 0\n" % (i, i, i)
			else:
				SHORTCUT	+=	"  CreateShortCut \"$SMPROGRAMS\\${PRODUCTNAME}\\${PRODUCTNAME%s}.lnk\" \"$INSTDIR\\bin\\${PRODUCTEXE%s}\" \"\" \"$INSTDIR\\bin\\${PRODUCTEXE%s}\" 0\n" % (i, i, i)

		PRODUCTEXE += "!define PRODUCTEXE	${PRODUCTEXE0}\n"

		str_sbfNSISTemplate = """\
; sbfNSISTemplate.nsi
;
; This script :
; - It will install files into a directory that the user selects
; - remember the installation directory (so if you install again, it will
; overwrite the old one automatically).
; - run as admin and installation occurs for all users
; - components chooser
; - has uninstall support
; - install/launch/uninstall Redistributable
; - and (optionally) installs start menu shortcuts (run all exe and uninstall).

; @todo write access on several directories
; @todo section with redistributable

; @todo mui
; @todo quicklaunch and desktop
; @todo repair/modify
; @todo LogSet on

;--------------------------------

!define SBFPROJECTNAME		"%s"
!define SBFPROJECTVERSION	"%s"

; PRODUCTNAME
%s
; PRODUCTEXE
%s
;--------------------------------

!include "redistributables.nsi"

;--------------------------------

; The name of the installer
Name "${PRODUCTNAME}"

; The file to write
OutFile "${SBFPROJECTNAME}_${SBFPROJECTVERSION}_setup.exe"

; The default installation directory
InstallDir $PROGRAMFILES\${PRODUCTNAME}

; Registry key to check for directory (so if you install again, it will
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\${PRODUCTNAME}" "Install_Dir"

; Request application privileges for Windows Vista
RequestExecutionLevel admin

;--------------------------------

; Pages

Page components
Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

;--------------------------------

; The stuff to install
Section "${PRODUCTNAME} core (required)"

  SectionIn RO

  SetShellVarContext all

  ; Set output path to the installation directory.
  SetOutPath $INSTDIR

  ; Put files there
!include "${SBFPROJECTNAME}_install_files.nsi"
  CreateDirectory "$INSTDIR\\var"

  ; Changes ACL
  ; From MSDN
  ; SID: S-1-5-32-545
  ; Name: Users
  ; Description: A built-in group.
  ; After the initial installation of the operating system, the only member is the Authenticated Users group.
  ; When a computer joins a domain, the Domain Users group is added to the Users group on the computer.

  AccessControl::GrantOnFile "$INSTDIR\share" "(S-1-5-32-545)" "GenericRead + GenericWrite"
;AccessControl::EnableFileInheritance "$INSTDIR\share"
  AccessControl::GrantOnFile "$INSTDIR\\var" "(S-1-5-32-545)" "FullAccess"
;AccessControl::EnableFileInheritance "$INSTDIR\\var"

  ; Redistributable
  CreateDirectory $INSTDIR\Redistributable
!insertmacro InstallRedistributableVCPP2005SP1
!insertmacro InstallRedistributableTscc

!insertmacro LaunchRedistributableVCPP2005SP1
!insertmacro LaunchRedistributableTscc

  ; Write the installation path into the registry
  WriteRegStr HKLM "SOFTWARE\${PRODUCTNAME}" "Install_Dir" "$INSTDIR"

  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCTNAME}" "DisplayName" "${PRODUCTNAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCTNAME}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCTNAME}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCTNAME}" "NoRepair" 1
  WriteUninstaller "uninstall.exe"

SectionEnd

; Optional section (can be disabled by the user)
Section "Start Menu Shortcuts"

  CreateDirectory "$SMPROGRAMS\${PRODUCTNAME}"

  SetOutPath $INSTDIR\\bin

%s
  CreateShortCut "$SMPROGRAMS\${PRODUCTNAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0

  SetOutPath $INSTDIR

SectionEnd

;--------------------------------

; Uninstaller

Section "Uninstall"

  SetShellVarContext all

  ; Remove files
!include "${SBFPROJECTNAME}_uninstall_files.nsi"
  RmDir "$INSTDIR\\var"

  ; Remove redistributable
!insertmacro RmRedistributableTscc
!insertmacro RmRedistributableVCPP2005SP1
  RmDir $INSTDIR\Redistributable

  ; Remove registry keys
  DeleteRegKey HKLM "SOFTWARE\${PRODUCTNAME}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCTNAME}"

  ; Remove uninstaller
  Delete $INSTDIR\uninstall.exe

  ; Remove installation directory
  RmDir $INSTDIR

  ; Remove shortcuts, if any
%s
  Delete "$SMPROGRAMS\${PRODUCTNAME}\*.*"
  ; Remove directories used
  RMDir "$SMPROGRAMS\${PRODUCTNAME}"

SectionEnd
""" % (env['sbf_project'], env['version'], PRODUCTNAME, PRODUCTEXE, SHORTCUT, UNINSTALL_SHORTCUT)
		file.write( str_sbfNSISTemplate )

def zipPrinterForNSISInstallFiles( target, source, env ):
	# Retrieves informations
	targetName = str( target[0] )
	sourceName = str( source[0] )
	parentOfSource = os.path.dirname( sourceName )

	encounteredFiles		= []
	encounteredDirectories	= []
	searchAllFilesAndDirectories( sourceName, encounteredFiles, encounteredDirectories )

	# Creates target file
	with open( targetName, 'w' ) as outputFile:
		# Creates directories
		for directory in encounteredDirectories:
			outputFile.write( "CreateDirectory \"$OUTDIR\%s\"\n" % convertPathAbsToRel(sourceName, directory) )

		# Copies files
		for file in encounteredFiles:
			outputFile.write( "File \"/oname=$OUTDIR\%s\" \"%s\"\n" % (convertPathAbsToRel(sourceName, file), file) )


def zipPrinterForNSISUninstallFiles( target, source, env ):
	# Retrieves informations
	targetName = str( target[0] )
	sourceName = str( source[0] )
	parentOfSource = os.path.dirname( sourceName )

	encounteredFiles		= []
	encounteredDirectories	= []
	searchAllFilesAndDirectories( sourceName, encounteredFiles, encounteredDirectories, walkTopDown = False )

	# Creates target file
	with open( targetName, 'w' ) as outputFile:
		# Removes files
		for file in encounteredFiles:
			outputFile.write( "Delete \"$INSTDIR\%s\"\n" % convertPathAbsToRel(sourceName, file) )

		# Removes directories
		for directory in encounteredDirectories:
			outputFile.write( "RmDir \"$INSTDIR\%s\"\n" % convertPathAbsToRel(sourceName, directory) )



def printZipPrinterForNSISInstallFiles( target, source, env ) :
	targetName = str(target[0])
	sourceName = str(source[0])
	return ("Generates %s (nsis install files) from %s" % (os.path.basename(targetName), sourceName) )

def printZipPrinterForNSISUninstallFiles( target, source, env ) :
	targetName = str(target[0])
	sourceName = str(source[0])
	return ("Generates %s (nsis uninstall files) from %s" % (os.path.basename(targetName), sourceName) )

def printZipPrinterForNSISGeneration( target, source, env ) :
	targetName = str(target[0])
	sourceName = str(source[0])
	return ("Generates %s (nsis main script)" % os.path.basename(targetName) )

### special zip related targets : zipRuntime, zipDeps, zipPortable, zipDev, zipSrc and zip ###
# @todo zip*_[build,install,clean,mrproper]
# @todo zip doxygen

def printZip( target, source, localenv ) :
	return '\n' + stringFormatter( localenv, "Create zip archives" )

def printZipRuntime( target, source, localenv ) :
	return '\n' + stringFormatter( localenv, "Create runtime package" )

def printZipDeps( target, source, localenv ) :
	return '\n' + stringFormatter( localenv, "Create deps package" )

def printZipPortable( target, source, localenv ) :
	return '\n' + stringFormatter( localenv, "Create portable package" )

def printZipDev( target, source, localenv ) :
	return '\n' + stringFormatter( localenv, "Create dev package" )

def printZipSrc( target, source, localenv ) :
	return '\n' + stringFormatter( localenv, "Create src package" )


def configureZipAndNSISTargets( env ):
	if (	('zipRuntime'		in env.sbf.myBuildTargets) or
			('zipDeps'			in env.sbf.myBuildTargets) or
			('zipPortable'		in env.sbf.myBuildTargets) or
			('zipDev'			in env.sbf.myBuildTargets) or
			('zipSrc'			in env.sbf.myBuildTargets) or
			('zip'				in env.sbf.myBuildTargets) or
			('nsis'				in env.sbf.myBuildTargets)	):
																								# FIXME: lazzy scons env construction => TODO: generalize (but must be optional)
		#
		sbf = env.sbf
		rootProjectEnv = sbf.myParsedProjects[env['sbf_project']]

		# Creates builders for zip and nsis
		# @todo Do the same without Builder ?
		# @todo Moves in sbfSevenZip.py and co

		env['SEVENZIP']			= '7z'
		# @todo checks win32 registry (idem for nsis)
		env['SEVENZIPPATH']		= "C:\\Program Files\\7-Zip"
		env['SEVENZIPCOM']		= "\"$SEVENZIPPATH\\$SEVENZIP\""
		env['SEVENZIPCOMSTR']	= "Zipping ${TARGET.file}"
		env['SEVENZIPADDFLAGS']	= "a -r"
		env['SEVENZIPFLAGS']	= "-bd"
		env['SEVENZIPSUFFIX']	= ".7z"
		env['BUILDERS']['SevenZipAdd'] = Builder( action = Action( "$SEVENZIPCOM $SEVENZIPADDFLAGS $SEVENZIPFLAGS $TARGET $SOURCE", env['SEVENZIPCOMSTR'] ) )

		import SCons																			# from SCons.Script.SConscript import SConsEnvironment
	#	zipBuilder = env.Builder(	action=Action(zipArchiver,printZipArchiver),
	#								source_factory=SCons.Node.FS.default_fs.Entry,
	#								target_factory=SCons.Node.FS.default_fs.Entry,
	#								multi=0 )
	#	env['BUILDERS']['zipArchiver'] = zipBuilder

		zipPrinterBuilder = env.Builder(	action=Action(zipPrinterForNSISInstallFiles, printZipPrinterForNSISInstallFiles),
											source_factory=SCons.Node.FS.default_fs.Entry,
											target_factory=SCons.Node.FS.default_fs.Entry,
											multi=0 )
		env['BUILDERS']['zipPrinterForNSISInstallFiles'] = zipPrinterBuilder

		zipPrinterBuilder = env.Builder(	action=Action(zipPrinterForNSISUninstallFiles, printZipPrinterForNSISUninstallFiles ),
											source_factory=SCons.Node.FS.default_fs.Entry,
											target_factory=SCons.Node.FS.default_fs.Entry,
											multi=0 )
		env['BUILDERS']['zipPrinterForNSISUninstallFiles'] = zipPrinterBuilder

		zipPrinterBuilder = rootProjectEnv.Builder(	action=Action(nsisGeneration, printZipPrinterForNSISGeneration ),
											source_factory=SCons.Node.FS.default_fs.Entry,
											target_factory=SCons.Node.FS.default_fs.Entry,
											multi=0 )
		rootProjectEnv['BUILDERS']['nsisGeneration'] = zipPrinterBuilder

		# compute zipPath (where files are copying before creating the zip file)
		# zipPathBase = /mnt/data/sbf/build/pak/vgsdk_0-4
		zipPakPath	=	os.path.join( sbf.myBuildPath, 'pak' )
		zipPathBase	=	os.path.join( zipPakPath, env['sbf_project'] + '_' + rootProjectEnv['version'] )

		# zipPath = zipPathBase + "_win32_cl7-1_D"
		zipPath		=	zipPathBase + sbf.my_Platform_myCCVersion + sbf.my_FullPostfix

		#_dev_2005_08_09
		runtimeZipPath	= zipPath		+ '_runtime_'	+ sbf.myDate
		depsZipPath		= zipPath		+ '_deps_'		+ sbf.myDate
		portableZipPath	= zipPath		+ '_portable_'	+ sbf.myDate
		devZipPath		= zipPath		+ '_dev_'		+ sbf.myDate
		srcZipPath		= zipPathBase	+ '_src_'		+ sbf.myDate

		#
		Alias( 'zip_print', env.Command('zip_print.out1', 'dummy.in', Action( nopAction, printZip ) ) )
		AlwaysBuild( 'zip_print' )

		Alias( 'zipRuntime_print',	env.Command('zipRuntime_print.out1','dummy.in',	Action( nopAction, printZipRuntime ) ) )
		Alias( 'zipDeps_print',		env.Command('zipDeps_print.out1','dummy.in',	Action( nopAction, printZipDeps ) ) )
		Alias( 'zipPortable_print',	env.Command('zipPortable_print.out1','dummy.in',Action( nopAction, printZipPortable ) ) )
		Alias( 'zipDev_print',		env.Command('zipDev_print.out1',	'dummy.in',	Action( nopAction, printZipDev ) ) )
		Alias( 'zipSrc_print',		env.Command('zipSrc_print.out1',	'dummy.in',	Action( nopAction, printZipSrc ) ) )

		Alias( 'zipRuntime',	['build', 'zip_print', 'zipRuntime_print'] )
		Alias( 'zipDeps',		['build', 'zip_print', 'zipDeps_print'] )
		Alias( 'zipPortable',	['build', 'zip_print', 'zipPortable_print'] )
		Alias( 'zipDev',		['build', 'zip_print', 'zipDev_print'] )
		Alias( 'zipSrc',		['build', 'zip_print', 'zipSrc_print'] )

		# Computes common root of all projects
		rootOfProjects = env.sbf.getProjectsRoot( rootProjectEnv )

		# Collects files to create the zip
		runtimeZipFiles 	= []
		depsZipFiles		= []
		portableZipFiles	= []
		devZipFiles			= []
		srcZipFiles			= []

		usesSet				= set()
		extension			= env['SHLIBSUFFIX']

		for projectName in sbf.myParsedProjects :
			lenv			= sbf.myParsedProjects[projectName]
			projectPathName	= lenv['sbf_projectPathName']
			project			= lenv['sbf_project']

			# Adds files to runtime and portable zip
			runtimeZipFiles		+= Install(	os.path.join(runtimeZipPath, 'bin'),	lenv['sbf_bin'] )
			runtimeZipFiles		+= Install(	os.path.join(runtimeZipPath, 'bin'),	lenv['sbf_lib_object'] )
			portableZipFiles	+= Install(	os.path.join(portableZipPath, 'bin'),	lenv['sbf_bin'] )
			portableZipFiles	+= Install(	os.path.join(portableZipPath, 'bin'),	lenv['sbf_lib_object'] )

			if len(lenv['sbf_share']) > 0:
				runtimeDestPath		= os.path.join(runtimeZipPath, 'share', project, lenv['version'])
				portableDestPath	= os.path.join(portableZipPath, 'share', project, lenv['version'])
				for file in lenv['sbf_share'] :
					runtimeZipFiles += InstallAs(	file.replace('share', runtimeDestPath, 1),
													os.path.join(projectPathName, file) )
					portableZipFiles+= InstallAs(	file.replace('share', portableDestPath, 1),
													os.path.join(projectPathName, file) )

			# Adds files to deps zip
	#		print ("Dependencies (only 'uses' option) for %s :" % project), lenv['uses']

			for element in lenv['uses']:
	#			if element not in usesSet:
	#				print ("Found a new dependency : %s" % element)
				usesSet.add( element )

			# Processes the 'stdlibs' project option
			if len(lenv['stdlibs']) > 0 :
				searchPathList = sbf.myLibInstallExtPaths[:]
				for stdlib in lenv['stdlibs'] :
					filename = os.path.splitext(stdlib)[0] + extension
					pathFilename = searchFileInDirectories( filename, searchPathList )
					if pathFilename:
						print("Found standard library %s" % pathFilename)
						depsZipFiles		+= Install( os.path.join(depsZipPath, 'bin'), pathFilename )
						portableZipFiles	+= Install( os.path.join(portableZipPath, 'bin'), pathFilename )
					else:
						print("Standard library %s not found (see 'stdlibs' project option of %s)." % (filename, projectName) )

			# Adds files to dev zip
			devZipFiles += Install(		os.path.join(devZipPath, 'bin'),			lenv['sbf_bin'] )

			for file in lenv['sbf_include'] :
				devZipFiles += InstallAs(	os.path.join(devZipPath, file),		os.path.join(projectPathName, file) )

			devZipFiles += Install( os.path.join(devZipPath, 'lib'), lenv['sbf_lib_object'] )
			devZipFiles += Install( os.path.join(devZipPath, 'lib'), lenv['sbf_lib_object_for_developer'] )

			# Adds files to src zip
			if lenv['vcsUse'] == 'yes' :
				allFiles = sbf.myVcs.getAllVersionedFiles( projectPathName )

				projectRelPath = convertPathAbsToRel( rootOfProjects, projectPathName )

				for absFile in allFiles:
					relFile = convertPathAbsToRel( projectPathName, absFile )
					srcZipFiles += InstallAs( os.path.join(srcZipPath, projectRelPath, relFile), absFile )
			# else nothing to do

		# Processes external dependencies
		listOfExternalDependencies = sorted(list(usesSet))
	#print ("List of external dependencies for %s :" % env['sbf_project'])

		# For each external dependency, do
		for useNameVersion in listOfExternalDependencies:
			# Extracts name and version of incoming external dependency
			useName, useVersion = UseRepository.extract( useNameVersion )
	#print ("%s = %s, %s" %(useNameVersion, useName, useVersion))

			# Retrieves use object for incoming dependency
			use = UseRepository.getUse( useName )
			if use != None :

				# Retrieves LIBS of incoming dependency
				libs = use.getLIBS( useVersion )
				if libs != None and len(libs) == 2:

					# Computes the search path list where libraries could be located
					searchPathList = sbf.myLibInstallExtPaths[:]
					libpath = use.getLIBPATH( useVersion )
					if (libpath != None) and (len(libpath) == 2) :
						if len(libpath[1]) > 0 :
							searchPathList.extend( libpath[1] )

					# For each library, do
					for file in libs[1]:
						filename = file + extension
						pathFilename = searchFileInDirectories( filename, searchPathList )
						if pathFilename:
							print ("Found library %s" % pathFilename)
							depsZipFiles		+= Install( os.path.join(depsZipPath, 'bin'), pathFilename )
							portableZipFiles	+= Install( os.path.join(portableZipPath, 'bin'), pathFilename )
						else:
							raise SCons.Errors.UserError( "File %s not found." % filename )
				else:
					raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s." % (useNameVersion, sbf.myPlatform) )

		runtimeZip = runtimeZipPath + env['SEVENZIPSUFFIX']
		Alias( 'zipRuntime_generate7z', env.SevenZipAdd( runtimeZip, Dir(runtimeZipPath) ) )
		Alias( 'zipRuntime',	[runtimeZipFiles, 'zipRuntime_generate7z'] )

		depsZip = depsZipPath + env['SEVENZIPSUFFIX']
		Alias( 'zipDeps_generate7z', env.SevenZipAdd( depsZip, Dir(depsZipPath) ) )
		Alias( 'zipDeps',		[depsZipFiles, 'zipDeps_generate7z'] )

		portableZip = portableZipPath + env['SEVENZIPSUFFIX']
		Alias( 'zipPortable_generate7z', env.SevenZipAdd( portableZip, Dir(portableZipPath) ) )
		Alias( 'zipPortable',	[portableZipFiles, 'zipPortable_generate7z' ] )

		devZip = devZipPath + env['SEVENZIPSUFFIX']
		Alias( 'zipDev_generate7z', env.SevenZipAdd( devZip, Dir(devZipPath) ) )
		Alias( 'zipDev',		[devZipFiles, 'zipDev_generate7z'] )

		if len(srcZipFiles) > 0:
			srcZip = srcZipPath + env['SEVENZIPSUFFIX']
			Alias( 'zipSrc_generate7z', env.SevenZipAdd( srcZip, Dir(srcZipPath) ) )
			Alias( 'zipSrc',	[srcZipFiles, 'zipSrc_generate7z'] )
		else:
			Alias( 'zipSrc',	srcZipFiles )

		if env['publishOn']:
	# @todo print message
			zipRsyncAction = env.createRsyncAction( os.path.basename(runtimeZip), File(runtimeZip), 'zipRuntime' )

			zipRsyncAction = env.createRsyncAction( os.path.basename(depsZip), File(depsZip), 'zipDeps' )

			zipRsyncAction = env.createRsyncAction( os.path.basename(portableZip), File(portableZip), 'zipPortable' )

			zipRsyncAction = env.createRsyncAction( os.path.basename(devZip), File(devZip), 'zipDev' )

			if len(srcZipFiles) > 0:
				zipRsyncAction = env.createRsyncAction( os.path.basename(srcZip), File(srcZip), 'zipSrc' )
			#else: nothing to do

		Alias( 'zip', ['zipRuntime', 'zipDeps', 'zipPortable', 'zipDev', 'zipSrc'] )

		Alias( 'nsis', ['build', portableZipFiles] )
		sbfRcNsisPath = os.path.join(env.sbf.mySCONS_BUILD_FRAMEWORK, 'rc', 'nsis' )
		Alias( 'nsis', env.Install( zipPakPath, os.path.join(sbfRcNsisPath, 'redistributables.nsi') ) )
		# @todo Creates a function to InstallAs( dirDest, dirSrc * )
		redistributableFiles = []
		searchFiles(	os.path.join(sbfRcNsisPath, 'Redistributable'),
						redistributableFiles,
						['.svn'] )
		installRedistributableFiles = []
		for file in redistributableFiles :
			installRedistributableFiles += env.InstallAs( os.path.join( zipPakPath, file.replace(sbfRcNsisPath + os.sep, '') ), file )
		Alias( 'nsis', installRedistributableFiles )
		nsisInstallFiles	= os.path.join( zipPakPath, rootProjectEnv['sbf_project'] + '_install_files.nsi' )
		nsisUninstallFile	= os.path.join( zipPakPath, rootProjectEnv['sbf_project'] + '_uninstall_files.nsi' )
		Alias( 'nsis', env.zipPrinterForNSISInstallFiles( nsisInstallFiles, portableZipPath ) )
		Alias( 'nsis', env.zipPrinterForNSISUninstallFiles(	nsisUninstallFile, portableZipPath ) )
		Alias( 'nsis', rootProjectEnv.nsisGeneration( portableZipPath + '.nsi', [nsisInstallFiles, nsisUninstallFile] ) )#portableZipPath + '.zip' ) )
		# @todo FIXME nsisRootPath
		# @todo Nsis builder
		nsisRootPath = "C:\\Program Files\\NSIS"
		nsisSetupFile = '%s_%s_setup.exe' % (env.sbf.myProject, env.sbf.myVersion)
		nsisBuildAction = env.Command(	nsisSetupFile, portableZipPath + '.nsi', #portableZipPath + '.exe'
										"\"%s\" $SOURCES" % os.path.join(nsisRootPath, 'makensis.exe' ) )
		Alias( 'nsis', nsisBuildAction )

		if env['publishOn'] :
			# @todo print message
			nsisRsyncAction = env.createRsyncAction( nsisSetupFile, File(os.path.join(zipPakPath, nsisSetupFile)), 'nsis' )
			env.Depends( nsisRsyncAction, nsisBuildAction )

		# @todo uses zip2exe on win32 ?
