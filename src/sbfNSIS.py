# SConsBuildFramework - Copyright (C) 2009, 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from __future__ import with_statement

from os.path import join

from src.sbfFiles	import *
#from src.sbfTools	import locateProgram
from src.sbfUses	import UseRepository
from src.sbfUI		import askQuestion
from src.SConsBuildFramework import stringFormatter, SConsBuildFramework, nopAction

from SCons.Script import *

# @todo always generated nsis files
# @todo uninstallRedist
# @todo Improves redist macros (adding message and with/without confirmation)


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
				products.append( lenv['sbf_project'] + lenv.sbf.my_PostfixLinkedToMyConfig )
				executables.append( os.path.basename(lenv['sbf_bin'][0]) )

		# Generates PRODUCTNAME
		PRODUCTNAME = ''
		for (i, product) in enumerate(products):
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
			PRODUCTEXE	+=	"!define PRODUCTEXE{0}	\"{1}\"\n".format( i, executable)
# @todo uses string.format()
			if i > 0:
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
!define SBFPROJECTCONFIG	"%s"

; PRODUCTNAME
%s
; PRODUCTEXE
%s
;--------------------------------



;--------------------------------

SetCompressor lzma

; The name of the installer
Name "${PRODUCTNAME}"

; The file to write
OutFile "${SBFPROJECTNAME}_${SBFPROJECTVERSION}${SBFPROJECTCONFIG}_setup.exe"

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

  ; Create 'var' directory
  CreateDirectory "$INSTDIR\\var"

  ; Changes ACL
  ; From MSDN
  ; SID: S-1-5-32-545
  ; Name: Users
  ; Description: A built-in group.
  ; After the initial installation of the operating system, the only member is the Authenticated Users group.
  ; When a computer joins a domain, the Domain Users group is added to the Users group on the computer.

;AccessControl::GrantOnFile "$INSTDIR\share" "(S-1-5-32-545)" "GenericRead + GenericWrite"
;AccessControl::EnableFileInheritance "$INSTDIR\share"
  AccessControl::GrantOnFile "$INSTDIR\\var" "(S-1-5-32-545)" "FullAccess"
;AccessControl::EnableFileInheritance "$INSTDIR\\var"

  ; Redistributable
  !include "${SBFPROJECTNAME}_redist.nsi"

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
!include "${SBFPROJECTNAME}_uninstall_redist.nsi"

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
""" % (env['sbf_project'], env['version'], env.sbf.my_PostfixLinkedToMyConfig, PRODUCTNAME, PRODUCTEXE, SHORTCUT, UNINSTALL_SHORTCUT)
		file.write( str_sbfNSISTemplate )



def redistGeneration( target, source, env ):
	"""target must be [${SBFPROJECTNAME}_redist.nsi , ${SBFPROJECTNAME}_uninstall_redist.nsi]"""

	# Retrieves/computes additional information
	targetNameRedist = str(target[0])
	targetNameUninstallRedist = str(target[1])

	sbf = env.sbf

	# compiler : CL90EXP or CL90 for example
	CLXYEXP = sbf.myCCVersion.replace( '-', '', 1 ).upper()

	uses = sorted(list( sbf.getAllUses(env) ))
	redistFiles = []

	for useNameVersion in uses:
		useName, useVersion = UseRepository.extract( useNameVersion )
		use = UseRepository.getUse( useName )
		if use:
			redistributables = use.getRedist( useVersion )
			for redistributable in redistributables:
				# '*.exe' launch executable,	('*.exe', 'question') ask and launch
				# '*.zip' extract in deps,		('*.zip', 'question') ask and extract
				if isinstance(redistributable, tuple):
					pass
				else:
					redistFiles.append(redistributable)

	# Open output file ${SBFPROJECTNAME}_redist.nsi
	with open( targetNameRedist, 'w' ) as file:
		file.write(
"""!include "redistributable.nsi"
!include "redistributableDatabase.nsi"
\n\n""" )

		# Redistributable for cl compiler
		file.write( "; Redistributable for cl compiler\n" )
		file.write( """!insertmacro InstallAndLaunchRedistributable "${{{0}}}"\n\n\n""".format(CLXYEXP) )

		# Redistributable for 'uses'
		if len(redistFiles)>0:
			file.write( "; Redistributable for 'uses'\n" )
			for redistFile in redistFiles:
				redistFileExtension = os.path.splitext(redistFile)[1]
				if redistFileExtension == '.zip':
					file.write( """!insertmacro InstallAndUnzipRedistributable "{0}" "$INSTDIR"\n""".format(redistFile.replace('/', '\\') ) )
				elif redistFileExtension == '.exe' :
					file.write( """!insertmacro InstallAndLaunchRedistributable "{0}"\n""".format(redistFile.replace('/', '\\') ) )
				else:
					raise SCons.Errors.StopError, "Unsupported type of redistributable {0}".format(redistFile)

	# Open output file ${SBFPROJECTNAME}_uninstall_redist.nsi
	with open( targetNameUninstallRedist, 'w' ) as file:
		pass
		# @todo

#!include "${SBFPROJECTNAME}_uninstall_redist.nsi"
#!insertmacro RmRedistributableTscc
#!insertmacro RmRedistributableVCPP2005SP1
#  RmDir $INSTDIR\Redistributable



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
	zipAndNSISTargets = set( ['zipruntime', 'zipdeps', 'zipportable', 'zipdev', 'zipsrc', 'zip', 'nsis'] )
	if len(zipAndNSISTargets & env.sbf.myBuildTargets) > 0:
		# Checks project exclusion to warn user
		if env['exclude'] and len(env['projectExclude'])>0:
			answer = askQuestion(	"WARNING: The following projects are excluded from the build : {0}\nWould you stop the process".format(env['projectExclude']),
									['yes', 'no'] )
			if answer == 'y':
				raise SCons.Errors.UserError( "Build interrupted by user." )
			#else continue the build

		# FIXME: lazzy scons env construction => TODO: generalize (but must be optional)
		#
		sbf = env.sbf
		rootProjectEnv = sbf.getRootProjectEnv()

		# Creates builders for zip and nsis
		# @todo Do the same without Builder ?
		# @todo Moves in sbfSevenZip.py and co

# @todo checks win32 registry (idem for nsis)
		env['SEVENZIP']			= '7z'
		env['SEVENZIPCOM']		= '\"{0}\"'.format( WhereIs('7z') )
		env['SEVENZIPCOMSTR']	= "Zipping ${TARGET.file}"
		env['SEVENZIPADDFLAGS']	= "a -r"
		env['SEVENZIPFLAGS']	= "-bd"
		env['SEVENZIPSUFFIX']	= ".7z"
		env['BUILDERS']['SevenZipAdd'] = Builder( action = Action( "$SEVENZIPCOM $SEVENZIPADDFLAGS $SEVENZIPFLAGS $TARGET $SOURCE" ) )#, env['SEVENZIPCOMSTR'] ) )

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

		zipPrinterBuilder = env.Builder(	action=Action(redistGeneration, printZipPrinterForNSISInstallFiles), # @todo printZipPrinterForNSISInstallFiles
											source_factory=SCons.Node.FS.default_fs.Entry,
											target_factory=SCons.Node.FS.default_fs.Entry,
											multi=0 )
		rootProjectEnv['BUILDERS']['redistGeneration'] = zipPrinterBuilder

		# compute zipPath (where files are copying before creating the zip file)
		# zipPathBase = /mnt/data/sbf/build/pak/vgsdk_0-4
		zipPakPath	=	join( sbf.myBuildPath, 'pak' )
		zipPathBase	=	join( zipPakPath, env['sbf_project'] + '_' + rootProjectEnv['version'] )

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

		Alias( 'zipRuntime_print',	env.Command('zipRuntime_print.out1',	'dummy.in',	Action( nopAction, printZipRuntime ) ) )
		Alias( 'zipDeps_print',		env.Command('zipDeps_print.out1',		'dummy.in',	Action( nopAction, printZipDeps ) ) )
		Alias( 'zipPortable_print',	env.Command('zipPortable_print.out1',	'dummy.in',Action( nopAction, printZipPortable ) ) )
		Alias( 'zipDev_print',		env.Command('zipDev_print.out1',		'dummy.in',	Action( nopAction, printZipDev ) ) )
		Alias( 'zipSrc_print',		env.Command('zipSrc_print.out1',		'dummy.in',	Action( nopAction, printZipSrc ) ) )

		Alias( 'zipruntime',	['infofile', 'build', 'zip_print', 'zipRuntime_print'] )
		Alias( 'zipdeps',		['build', 'zip_print', 'zipDeps_print'] )
		Alias( 'zipportable',	['infofile', 'build', 'zip_print', 'zipPortable_print'] )
		Alias( 'zipdev',		['build', 'zip_print', 'zipDev_print'] )
		Alias( 'zipsrc',		['build', 'zip_print', 'zipSrc_print'] )

		# Computes common root of all projects
		rootOfProjects = env.sbf.getProjectsRoot( rootProjectEnv )

		# Collects files to create the zip
		runtimeZipFiles 	= []
		depsZipFiles		= []
		portableZipFiles	= []
		devZipFiles			= []
		srcZipFiles			= []

		# Creates 'var' directory
		varDirectory = join(runtimeZipPath, 'var')
		runtimeZipFiles += Command('zipRuntime_mkdirVar.out', 'dummy.in', [Delete(varDirectory), Mkdir(varDirectory)] )
		varDirectory = join(portableZipPath, 'var')
		portableZipFiles += Command('zipPortable_mkdirVar.out', 'dummy.in', [Delete(varDirectory), Mkdir(varDirectory)] )

		#
		usesSet					= set()
		extension				= env['SHLIBSUFFIX']
		licenseInstallExtPaths	= [ join(element, 'license') for element in sbf.myInstallExtPaths ]

		for projectName in sbf.myParsedProjects :
			lenv			= sbf.myParsedProjects[projectName]
			projectPathName	= lenv['sbf_projectPathName']
			project			= lenv['sbf_project']

			# Adds files to runtime and portable zip
			runtimeZipFiles		+= Install(	join(runtimeZipPath, 'bin'),	lenv['sbf_bin'] )
			runtimeZipFiles		+= Install(	join(runtimeZipPath, 'bin'),	lenv['sbf_lib_object'] )
			portableZipFiles	+= Install(	join(portableZipPath, 'bin'),	lenv['sbf_bin'] )
			portableZipFiles	+= Install(	join(portableZipPath, 'bin'),	lenv['sbf_lib_object'] )

			runtimeDestPath		= join(runtimeZipPath, 'share', project, lenv['version'])
			portableDestPath	= join(portableZipPath, 'share', project, lenv['version'])
			for file in lenv.get('sbf_share', []):
				runtimeZipFiles += InstallAs(	file.replace('share', runtimeDestPath, 1),
												join(projectPathName, file) )
				portableZipFiles+= InstallAs(	file.replace('share', portableDestPath, 1),
												join(projectPathName, file) )

			for file in lenv.get('sbf_info', []):
				runtimeZipFiles += Install( runtimeDestPath, file )
				portableZipFiles += Install( portableDestPath, file )

			# Adds files to deps zip
	#		print ("Dependencies (only 'uses' option) for %s :" % project), lenv['uses']

			for element in lenv['uses']:
	#			if element not in usesSet:
	#				print ("Found a new dependency : %s" % element)
				usesSet.add( element )

			# Processes the 'stdlibs' project option
			if len(lenv['stdlibs']) > 0:
				searchPathList = sbf.myLibInstallExtPaths[:]
				for stdlib in lenv['stdlibs']:
					filename = os.path.splitext(stdlib)[0] + extension
					pathFilename = searchFileInDirectories( filename, searchPathList )
					if pathFilename:
						print("Found standard library %s" % pathFilename)
						depsZipFiles		+= Install( join(depsZipPath, 'bin'), pathFilename )
						portableZipFiles	+= Install( join(portableZipPath, 'bin'), pathFilename )
					else:
						print("Standard library %s not found (see 'stdlibs' project option of %s)." % (filename, projectName) )

			# Adds files to dev zip
			devZipFiles += Install(		join(devZipPath, 'bin'),			lenv['sbf_bin'] )

			for file in lenv['sbf_include'] :
				devZipFiles += InstallAs(	join(devZipPath, file),		join(projectPathName, file) )

			devZipFiles += Install( join(devZipPath, 'lib'), lenv['sbf_lib_object'] )
			devZipFiles += Install( join(devZipPath, 'lib'), lenv['sbf_lib_object_for_developer'] )

			# Adds files to src zip
			if lenv['vcsUse'] == 'yes' :
				allFiles = sbf.myVcs.getAllVersionedFiles( projectPathName )

				projectRelPath = convertPathAbsToRel( rootOfProjects, projectPathName )

				for absFile in allFiles:
					relFile = convertPathAbsToRel( projectPathName, absFile )
					srcZipFiles += InstallAs( join(srcZipPath, projectRelPath, relFile), absFile )
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
			if use:

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
							depsZipFiles		+= Install( join(depsZipPath, 'bin'), pathFilename )
							portableZipFiles	+= Install( join(portableZipPath, 'bin'), pathFilename )
						else:
							raise SCons.Errors.UserError( "File %s not found." % filename )
				else:
					raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s." % (useNameVersion, sbf.myPlatform) )

				# Retrieves license file(s) of incoming dependency
				# from IUse class
				warningAboutLicense = True
				licenses = use.getLicenses( useVersion )
				if licenses and len(licenses)>0:
					for filename in licenses:
						pathFilename = searchFileInDirectories( filename, licenseInstallExtPaths )
						if pathFilename:
							print ("Found license %s" % pathFilename)
							warningAboutLicense = False
							depsZipFiles		+= Install( join(depsZipPath, 'license'), pathFilename )
							portableZipFiles	+= Install( join(portableZipPath, 'license'), pathFilename )
						else:
							raise SCons.Errors.UserError( "File %s not found." % filename )
				# else: warningAboutLicense = True

				# implicit license file(s) if any
				# license file without prefix (case: only one license file)
				licenses = ['license.{0}{1}.txt'.format( useName, useVersion)]
				# license file with prefix (case: several license files)
				for prefix in range(9):
					licenses += ['{0}license.{1}{2}.txt'.format( prefix, useName, useVersion)]
				for filename in licenses:
					pathFilename = searchFileInDirectories( filename, licenseInstallExtPaths )
					if pathFilename:
						print ("Found license %s" % pathFilename)
						warningAboutLicense = False
						depsZipFiles		+= Install( join(depsZipPath, 'license'), pathFilename )
						portableZipFiles	+= Install( join(portableZipPath, 'license'), pathFilename )
					#else:
					#	raise SCons.Errors.UserError( "File %s not found." % filename )
				# Prints warning if needed
				if warningAboutLicense:
					print ('sbfWarning: No license file for {0}'.format(useNameVersion))

		runtimeZip = runtimeZipPath + env['SEVENZIPSUFFIX']
		Alias( 'zipRuntime_generate7z', env.SevenZipAdd( runtimeZip, Dir(runtimeZipPath) ) )
		Alias( 'zipruntime',	[runtimeZipFiles, 'zipRuntime_generate7z'] )

		depsZip = depsZipPath + env['SEVENZIPSUFFIX']
		Alias( 'zipDeps_generate7z', env.SevenZipAdd( depsZip, Dir(depsZipPath) ) )
		Alias( 'zipdeps',		[depsZipFiles, 'zipDeps_generate7z'] )

		portableZip = portableZipPath + env['SEVENZIPSUFFIX']
		Alias( 'zipPortable_generate7z', env.SevenZipAdd( portableZip, Dir(portableZipPath) ) )
		Alias( 'zipportable',	[portableZipFiles, 'zipPortable_generate7z'] )

		devZip = devZipPath + env['SEVENZIPSUFFIX']
		Alias( 'zipDev_generate7z', env.SevenZipAdd( devZip, Dir(devZipPath) ) )
		Alias( 'zipdev',		[devZipFiles, 'zipDev_generate7z'] )

		if len(srcZipFiles) > 0:
			srcZip = srcZipPath + env['SEVENZIPSUFFIX']
			Alias( 'zipSrc_generate7z', env.SevenZipAdd( srcZip, Dir(srcZipPath) ) )
			Alias( 'zipsrc',	[srcZipFiles, 'zipSrc_generate7z'] )
		else:
			Alias( 'zipsrc',	srcZipFiles )

		if env['publishOn']:
	# @todo print message
			zipRsyncAction = env.createRsyncAction( os.path.basename(runtimeZip), File(runtimeZip), 'zipruntime' )

			zipRsyncAction = env.createRsyncAction( os.path.basename(depsZip), File(depsZip), 'zipdeps' )

			zipRsyncAction = env.createRsyncAction( os.path.basename(portableZip), File(portableZip), 'zipportable' )

			zipRsyncAction = env.createRsyncAction( os.path.basename(devZip), File(devZip), 'zipdev' )

			if len(srcZipFiles) > 0:
				zipRsyncAction = env.createRsyncAction( os.path.basename(srcZip), File(srcZip), 'zipsrc' )
			#else: nothing to do

		Alias( 'zip', ['zipruntime', 'zipdeps', 'zipportable', 'zipdev', 'zipsrc'] )

		### nsis target ###

		Alias( 'nsis', ['infofile', 'build', portableZipFiles] ) # @todo uses 'zipportable' and @todo check order 'build', 'infofile'

		# Copies redistributable related files
		sbfNSISPath = join(env.sbf.mySCONS_BUILD_FRAMEWORK, 'NSIS' )
		sbfRcNsisPath = join(env.sbf.mySCONS_BUILD_FRAMEWORK, 'rc', 'nsis' )
		Alias( 'nsis', env.Install( zipPakPath, join(sbfNSISPath, 'redistributable.nsi') ) )
		Alias( 'nsis', env.Install( zipPakPath, join(sbfRcNsisPath, 'redistributableDatabase.nsi') ) )

		# @todo Creates a function to InstallAs( dirDest, dirSrc * )
		redistributableFiles = []
		searchFiles(	join(sbfRcNsisPath, 'Redistributable'),
						redistributableFiles,
						['.svn'] )

		installRedistributableFiles = []
		for file in redistributableFiles :
			installRedistributableFiles += env.InstallAs( join( zipPakPath, file.replace(sbfRcNsisPath + os.sep, '') ), file )
		# endtodo
		Alias( 'nsis', installRedistributableFiles )

		# Generates several nsis files
		nsisRedistFiles		=	[ join( zipPakPath, rootProjectEnv['sbf_project'] + '_redist.nsi' ), join( zipPakPath, rootProjectEnv['sbf_project'] + '_uninstall_redist.nsi' ) ]
		nsisInstallFiles	= join( zipPakPath, rootProjectEnv['sbf_project'] + '_install_files.nsi' )
		nsisUninstallFile	= join( zipPakPath, rootProjectEnv['sbf_project'] + '_uninstall_files.nsi' )
		Alias( 'nsis', rootProjectEnv.redistGeneration( nsisRedistFiles, portableZipPath ) )
		Alias( 'nsis', env.zipPrinterForNSISInstallFiles( nsisInstallFiles, portableZipPath ) )
		Alias( 'nsis', env.zipPrinterForNSISUninstallFiles(	nsisUninstallFile, portableZipPath ) )
		Alias( 'nsis', rootProjectEnv.nsisGeneration( portableZipPath + '.nsi', [nsisRedistFiles, nsisInstallFiles, nsisUninstallFile] ) )#portableZipPath + '.zip' ) )

# @todo Nsis builder
		nsisRootPath = "C:\\Program Files\\NSIS"
		#nsisRootPath = locateProgram( 'nsis' )
		nsisSetupFile = '%s_%s_setup.exe' % (env.sbf.myProject, env.sbf.myVersion)
		nsisBuildAction = env.Command(	nsisSetupFile, portableZipPath + '.nsi', #portableZipPath + '.exe'
										"\"%s\" $SOURCES" % join(nsisRootPath, 'makensis.exe' ) )
		Alias( 'nsis', nsisBuildAction )

		if env['publishOn'] :
			# @todo print message
			nsisRsyncAction = env.createRsyncAction( nsisSetupFile, File(join(zipPakPath, nsisSetupFile)), 'nsis' )
			env.Depends( nsisRsyncAction, nsisBuildAction )

		# @todo uses zip2exe on win32 ?
