# SConsBuildFramework - Copyright (C) 2009, 2010, 2011, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from os.path import join, splitext

from src.sbfArchives import extractArchive, isExtractionSupported
from src.sbfFiles	import *
from src.sbfTools	import locateProgram
from src.sbfUses	import UseRepository
from src.sbfUtils	import capitalize
from src.sbfUI		import askQuestion
from src.sbfVersion import splitUsesName
from src.SConsBuildFramework import stringFormatter, SConsBuildFramework, nopAction

from SCons.Script import *


# @todo debug zipsrc if a used file is no more under vcs.
# @todo Improves redist macros (adding message and with/without confirmation)
# @todo improves output


def nsisGeneration( target, source, env ):

	# Retrieves/computes additional information
	targetName = str(target[0])

	# Open output file
	with open( targetName, 'w' ) as file:
		# Retrieves informations (all executables, ...)
		products	= []
		executables	= []
		rootProject	= ''
		for (projectName, lenv) in env.sbf.myParsedProjects.iteritems():
			if lenv['type'] == 'exec' :
				#print lenv['sbf_project'], os.path.basename(lenv['sbf_bin'][0])
				if len(products) == 0:
					rootProject = lenv['sbf_project']
				products.append( capitalize(lenv['sbf_project']) + lenv.sbf.my_PostfixLinkedToMyConfig )
				executables.append( os.path.basename(lenv['sbf_bin'][0]) )

		# Generates PRODUCTNAME
		PRODUCTNAME = ''
		for (i, product) in enumerate(products):
			PRODUCTNAME += "!define PRODUCTNAME%s	\"%s\"\n" % (i, product)
		PRODUCTNAME += "!define PRODUCTNAME	${PRODUCTNAME0}\n"

		# Generates PRODUCTEXE, SHORTCUT, DESKTOPSHORTCUT, QUICKLAUNCHSHORTCUT, UNINSTALL_SHORTCUT, UNINSTALL_DESKTOPSHORTCUT and UNINSTALL_QUICKLAUNCHSHORTCUT
		PRODUCTEXE						= ''
		SHORTCUT						= ''
		DESKTOPSHORTCUT					= ''
		QUICKLAUNCHSHORTCUT				= ''
		UNINSTALL_SHORTCUT				= ''
		UNINSTALL_DESKTOPSHORTCUT		= ''
		UNINSTALL_QUICKLAUNCHSHORTCUT	= ''
		if len(executables) > 1 :
			SHORTCUT = '  CreateDirectory \"${STARTMENUROOT}\\tools\"\n'
			UNINSTALL_SHORTCUT	=	'  Delete \"${STARTMENUROOT}\\tools\\*.*\"\n'
			UNINSTALL_SHORTCUT	+=	'  RMDir \"${STARTMENUROOT}\\tools\"\n'

		for (i, executable) in enumerate(executables) :
			PRODUCTEXE	+=	"!define PRODUCTEXE{0}	\"{1}\"\n".format( i, executable)
			if i > 0:
				SHORTCUT	+=	'  SetOutPath \"$INSTDIR\\bin\"\n'
				SHORTCUT	+=	"  CreateShortCut \"${STARTMENUROOT}\\tools\\${PRODUCTNAME%s}.lnk\" \"$INSTDIR\\bin\\${PRODUCTEXE%s}\" \"\" \"$INSTDIR\\bin\\${PRODUCTEXE%s}\" 0\n" % (i, i, i)
			else:
				SHORTCUT						=	'  SetOutPath \"$INSTDIR\\bin\"\n'
				SHORTCUT						+=	'  CreateShortCut \"${STARTMENUROOT}\\${PRODUCTNAME0}.lnk\" \"$INSTDIR\\bin\\${PRODUCTEXE0}\" \"\" \"$INSTDIR\\bin\\${PRODUCTEXE0}\" 0\n'
				DESKTOPSHORTCUT					=	'  SetOutPath \"$INSTDIR\\bin\"\n'
				DESKTOPSHORTCUT					+=	'  CreateShortCut \"$DESKTOP\\${PRODUCTNAME0}.lnk\" \"$INSTDIR\\bin\\${PRODUCTEXE0}\" \"\" \"$INSTDIR\\bin\\${PRODUCTEXE0}\" 0\n'
				QUICKLAUNCHSHORTCUT				=	'  CreateShortCut \"$QUICKLAUNCH\\${PRODUCTNAME0}.lnk\" \"$INSTDIR\\bin\\${PRODUCTEXE0}\" \"\" \"$INSTDIR\\bin\\${PRODUCTEXE0}\" 0\n'
				UNINSTALL_DESKTOPSHORTCUT		=	'  Delete \"$DESKTOP\\${PRODUCTNAME0}.lnk\"\n'
				UNINSTALL_QUICKLAUNCHSHORTCUT	=	'  Delete \"$QUICKLAUNCH\\${PRODUCTNAME0}.lnk\"\n'

		PRODUCTEXE += "!define PRODUCTEXE	${PRODUCTEXE0}\n"

		# Generates ICON
		ICON = "; no icon"
		if rootProject:
			lenv = env.sbf.myParsedProjects[rootProject]
			iconFile = os.path.join( lenv['sbf_projectPathName'], 'rc', lenv['sbf_project']+'.ico')
			if os.path.exists( iconFile ):
				ICON = 'Icon "{0}"'.format( iconFile )
			#else: ICON = "; no icon"

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
; - install/launch/uninstall Visual C++ redistributable and sbfPak redistributable.
; - installs start menu shortcuts (run all exe and uninstall).
; - (optionally) installs desktop menu shortcut for the main executable.
; @todo Uses UAC to - and (optionally) installs quicklaunch menu shortcuts for the main executable.
; - prevent running multiple instances of the installer

; @todo write access on several directories
; @todo section with redistributable

; @todo mui
; @todo quicklaunch
; @todo repair/modify
; @todo LogSet on


;--------------------------------

!include "FileFunc.nsh"

SetCompressor lzma

!define SBFPROJECTNAME				"{projectName}"
!define SBFPROJECTNAMECAPITALIZED	"{projectNameCapitalized}"
!define SBFPROJECTVERSION			"{projectVersion}"
!define SBFPROJECTCONFIG			"{projectConfig}"
!define SBFPROJECTVENDOR			"{projectVendor}"
!define SBFDATE						"{date}"

; SETUPFILE
!define SETUPFILE "${{SBFPROJECTNAMECAPITALIZED}}_${{SBFPROJECTVERSION}}${{SBFPROJECTCONFIG}}_${{SBFDATE}}_setup.exe"

;
!define REGKEYROOT		"Software\${{SBFPROJECTVENDOR}}\${{PRODUCTNAME}}"
!define STARTMENUROOT	"$SMPROGRAMS\${{SBFPROJECTVENDOR}}\${{PRODUCTNAME}}"

; PRODUCTNAME
{productName}

; PRODUCTEXE
{productExe}

;--------------------------------

Function .onInit
 System::Call 'kernel32::CreateMutexA(i 0, i 0, t "${{SETUPFILE}}") i .r1 ?e'
 Pop $R0
 StrCmp $R0 0 +3
 MessageBox MB_OK|MB_ICONSTOP "The installer is already running."
 Abort
FunctionEnd

;--------------------------------

; The name of the installer
Name "${{PRODUCTNAME}}"

; Version information
VIAddVersionKey "ProductName" "${{PRODUCTNAME}}"
VIAddVersionKey "CompanyName" "${{SBFPROJECTVENDOR}}"
VIAddVersionKey "LegalCopyright" "(C) ${{SBFPROJECTVENDOR}}"
VIAddVersionKey "FileDescription" "{projectDescription}"
VIAddVersionKey "FileVersion" "{productVersion}"
VIAddVersionKey "ProductVersion" "{productVersion}"

VIProductVersion "{productVersion}"

; icon of the installer
{icon}

; The file to write
OutFile "${{SETUPFILE}}"

; The default installation directory
; @todo InstallDir should be configurable
; InstallDir "$PROGRAMFILES\${{PRODUCTNAME}}"
; InstallDir "$PROGRAMFILES\${{SBFPROJECTVENDOR}}\${{PRODUCTNAME}}"
InstallDir "$PROGRAMFILES\${{SBFPROJECTVENDOR}}\${{PRODUCTNAME}}\${{SBFPROJECTVERSION}}"

; Registry key to check for directory (so if you install again, it will
; overwrite the old one automatically)
InstallDirRegKey HKLM "${{REGKEYROOT}}" "Install_Dir"

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
Section "${{PRODUCTNAME}} core (required)"
  SectionIn RO

  SetShellVarContext all

  ; Set output path to the installation directory.
  SetOutPath $INSTDIR

  ; Backups 'var' directory if already present
  ${{GetTime}} "" "L" $0 $1 $2 $6 $3 $4 $5
  CopyFiles /SILENT "$INSTDIR\\var" "$INSTDIR\\var_backup_$0-$1-$2_$3-$4-$5"
  RmDir /r "$INSTDIR\\var"

  ; Put files there
  !include "${{SBFPROJECTNAME}}_install_files.nsi"
 
  ; 'var' directory is created by SBFPROJECTNAME_install_files.nsi

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
  !include "${{SBFPROJECTNAME}}_install_redist.nsi"

  ; Write the installation path into the registry
  WriteRegStr HKLM "${{REGKEYROOT}}" "Install_Dir" "$INSTDIR"

  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${{PRODUCTNAME}}" "DisplayIcon" '"$INSTDIR\\bin\\${{PRODUCTEXE}}"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${{PRODUCTNAME}}" "DisplayName" "${{SBFPROJECTVENDOR}} ${{PRODUCTNAME}} ${{SBFPROJECTVERSION}}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${{PRODUCTNAME}}" "DisplayVersion" "${{SBFPROJECTVERSION}}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${{PRODUCTNAME}}" "Publisher" "${{SBFPROJECTVENDOR}}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${{PRODUCTNAME}}" "UninstallString" '"$INSTDIR\\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${{PRODUCTNAME}}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${{PRODUCTNAME}}" "NoRepair" 1
  WriteUninstaller "uninstall.exe"

SectionEnd



Section "Start Menu Shortcuts"
  SectionIn RO

  SetShellVarContext all
  CreateDirectory "${{STARTMENUROOT}}"
{startMenuShortcuts}
  CreateShortCut "${{STARTMENUROOT}}\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
SectionEnd


; Optional section (can be disabled by the user)
Section "Shortcut on desktop"

  SetShellVarContext all
 
{desktopShortcuts}

SectionEnd


;--------------------------------
; Uninstaller

Section "Uninstall"

  SetShellVarContext all

  ; Remove files
  !include "${{SBFPROJECTNAME}}_uninstall_files.nsi"

  ; Remove redistributable
  !include "${{SBFPROJECTNAME}}_uninstall_redist.nsi"

  ; Remove registry keys
  DeleteRegKey HKLM "${{REGKEYROOT}}"
  DeleteRegKey /ifempty HKLM "Software\${{SBFPROJECTVENDOR}}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${{PRODUCTNAME}}"

  ; Remove uninstaller
  Delete $INSTDIR\uninstall.exe

  ; Remove installation directory
  RmDir $INSTDIR

  ; Remove shortcuts, if any
{removeStartMenuShortcuts}
  Delete "${{STARTMENUROOT}}\*.*"
  ; Remove directories used
  RMDir "${{STARTMENUROOT}}"
  RMDir "$SMPROGRAMS\${{SBFPROJECTVENDOR}}"
 
{removeDesktopShortcuts}
 
SectionEnd
""".format(	projectName=env['sbf_project'],
			projectNameCapitalized=capitalize(env['sbf_project']),
			projectVersion=env['version'],
			projectConfig=env.sbf.my_PostfixLinkedToMyConfig,
			projectVendor=env.sbf.myCompanyName,
			projectDescription=env['description'],
			date=env.sbf.myDate,
			productName=PRODUCTNAME,
			productExe=PRODUCTEXE,
			productVersion='{0}.{1}.{2}.0'.format( env['sbf_version_major'], env['sbf_version_minor'], env['sbf_version_maintenance'] ),
			icon=ICON,
			startMenuShortcuts=SHORTCUT,
			desktopShortcuts=DESKTOPSHORTCUT,
#			quicklaunchShortcuts=QUICKLAUNCHSHORTCUT,
			removeStartMenuShortcuts=UNINSTALL_SHORTCUT,
			removeDesktopShortcuts=UNINSTALL_DESKTOPSHORTCUT,
#			removeQuicklaunchShortcuts=UNINSTALL_QUICKLAUNCHSHORTCUT
			)

		file.write( str_sbfNSISTemplate )


def redistGeneration( target, source, env ):
	"""target must be [${SBFPROJECTNAME}_redist.nsi , ${SBFPROJECTNAME}_uninstall_redist.nsi]"""

	# Retrieves/computes additional information
	targetNameRedist = str(target[0])
	targetNameUninstallRedist = str(target[1])

	sbf = env.sbf

	# compiler : CL90EXP or CL90 for example
	CLXYEXP = sbf.myCCVersion.replace( '-', '', 1 ).upper()

	# dependencies
	uses = sorted(list( sbf.getAllUses(env) ))
	redistFiles = []

# @remark no more used, because redistributables are already unzip in zipPortable
#	for useNameVersion in uses:
#		useName, useVersion = splitUsesName( useNameVersion )
#		use = UseRepository.getUse( useName )
#		if use:
#			redistributables = use.getRedist( useVersion )
#			for redistributable in redistributables:
				# '*.exe' launch executable,	('*.exe', 'question') ask and launch
				# '*.zip' extract in deps,		('*.zip', 'question') ask and extract
#				if isinstance(redistributable, tuple):
#					pass
#				else:
#					redistFiles.append(redistributable)


	# Open output file ${SBFPROJECTNAME}_redist.nsi
	with open( targetNameRedist, 'w' ) as file:
		file.write(
"""!include "redistributable.nsi"
!include "redistributableDatabase.nsi"
\n\n""" )

		# Redistributable for cl compiler
		file.write( "; Redistributable for cl compiler\n" )
		if sbf.myCCVersion >= 9.0:
			file.write( """!insertmacro InstallAndLaunchRedistributableQ "${{{file}}}" "{options}"\n\n\n""".format(file=CLXYEXP, options="/q") )
		else:
			file.write( """!insertmacro InstallAndLaunchRedistributableQ "${{{file}}}" ""\n\n\n""".format(file=CLXYEXP) )

# @remark no more used, because redistributables are already unzip in zipPortable
#		# Redistributable for 'uses'
#		if len(redistFiles)>0:
#			file.write( "; Redistributable for 'uses'\n" )
#			for redistFile in redistFiles:
#				redistFileExtension = splitext(redistFile)[1]
#				if redistFileExtension == '.zip':
#					file.write( """!insertmacro InstallAndUnzipRedistributable "{0}" "$INSTDIR"\n""".format(redistFile.replace('/', '\\') ) )
#				elif redistFileExtension == '.exe' :
#					file.write( """!insertmacro InstallAndLaunchRedistributable "{0}"\n""".format(redistFile.replace('/', '\\') ) )
#				else:
#					raise SCons.Errors.StopError, "Unsupported type of redistributable {0}".format(redistFile)


	# Open output file ${SBFPROJECTNAME}_uninstall_redist.nsi
	with open( targetNameUninstallRedist, 'w' ) as file:
		# Redistributable for cl compiler
		file.write( "; Redistributable for cl compiler\n" )
		file.write( """!insertmacro RmRedistributable "${{{file}}}"\n\n\n""".format(file=CLXYEXP) )



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

def printNsisGeneration( target, source, env ) :
	targetName = str(target[0])
	sourceName = str(source[0])
	return ("Generates %s (nsis main script)" % os.path.basename(targetName) )

def printRedistGeneration( target, source, env ) :
	targetName = str(target[0])
	sourceName = str(source[0])
	return ("Generates %s (redist files)" % os.path.basename(targetName) )

### special zip related targets : zipRuntime, zipDeps, portable, zipPortable, zipDev, zipSrc and zip ###
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
	zipAndNSISTargets = set( ['zipruntime', 'zipdeps', 'portable', 'zipportable', 'zipdev', 'zipsrc', 'zip', 'nsis'] )
	cleanAndMrproperTargets = set( ['zip_clean', 'zip_mrproper', 'nsis_clean', 'nsis_mrproper'] )
	allTargets = zipAndNSISTargets | cleanAndMrproperTargets

	if	len(cleanAndMrproperTargets & env.sbf.myBuildTargets) > 0:
		env.SetOption('clean', 1)

	if len(allTargets & env.sbf.myBuildTargets) > 0:
		# Checks project exclusion to warn user
		if env['exclude'] and len(env['projectExclude'])>0:
			answer = askQuestion(	"WARNING: The following projects are excluded from the build : {0}\nWould you continue the process".format(env['projectExclude']),
									['yes', 'no'], env['queryUser'] )
			if answer == 'n':
				raise SCons.Errors.UserError( "Build interrupted by user." )
			#else continue the build
		
		# lazzy scons env construction => @todo generalize (but must be optional)
		sbf = env.sbf
		rootProjectEnv = sbf.getRootProjectEnv()

		# @todo Moves in sbfSevenZip.py and co
		sevenzipLocation = locateProgram('7z')
		env['SEVENZIPCOM']		= '\"{0}\"'.format( join(sevenzipLocation, '7z' ) )
		env['SEVENZIPCOMSTR']	= "Zipping ${TARGET.file}"
		env['SEVENZIPADDFLAGS']	= "a -r"
		env['SEVENZIPFLAGS']	= "-bd"
		env['SEVENZIPSUFFIX']	= ".7z"
		env['BUILDERS']['SevenZipAdd'] = Builder( action = Action( "$SEVENZIPCOM $SEVENZIPADDFLAGS $SEVENZIPFLAGS $TARGET $SOURCE" ) )#, env['SEVENZIPCOMSTR'] ) )

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
		Alias( 'portable_print',	env.Command('portable_print.out1',		'dummy.in',Action( nopAction, printZipPortable ) ) )
		Alias( 'zipPortable_print',	env.Command('zipPortable_print.out1',	'dummy.in',Action( nopAction, printZipPortable ) ) )
		Alias( 'zipDev_print',		env.Command('zipDev_print.out1',		'dummy.in',	Action( nopAction, printZipDev ) ) )
		Alias( 'zipSrc_print',		env.Command('zipSrc_print.out1',		'dummy.in',	Action( nopAction, printZipSrc ) ) )

		Alias( 'zipruntime',	['infofile', 'build', 'zip_print', 'zipRuntime_print'] )
		Alias( 'zipdeps',		['build', 'zip_print', 'zipDeps_print'] )
		Alias( 'portable',		['infofile', 'build', 'zip_print', 'zipPortable_print'] )
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

		# Removes directories containing zip* files.
		# @todo deferred delete
		Execute([ Delete(runtimeZipPath), Delete(depsZipPath), Delete(portableZipPath), Delete(devZipPath), Delete(srcZipPath) ])

		# Creates 'var' directory
		varDirectory = join(runtimeZipPath, 'var')
		runtimeZipFiles += Command('zipRuntime_mkdirVar.out', 'dummy.in', [Delete(varDirectory), Mkdir(varDirectory)] )
		varDirectory = join(portableZipPath, 'var')
		portableZipFiles += Command('zipPortable_mkdirVar.out', 'dummy.in', [Delete(varDirectory), Mkdir(varDirectory)] )

		#
		licenseInstallExtPaths	= [ join(element, 'license') for element in sbf.myInstallExtPaths ]

		#
		# Processes projects built with sbf
		#
		for projectName in sbf.myParsedProjects:
			lenv			= sbf.getEnv(projectName)
			projectPathName	= lenv['sbf_projectPathName']
			project			= lenv['sbf_project']

			runtimeDestPath		= join(runtimeZipPath, 'share', project, lenv['version'])
			portableDestPath	= join(portableZipPath, 'share', project, lenv['version'])

			# Adds executables and libraries
			if 'sbf_bin' in lenv:
				runtimeZipFiles		+= Install( join(runtimeZipPath, 'bin'),	lenv['sbf_bin'] )
				portableZipFiles	+= Install( join(portableZipPath, 'bin'),	lenv['sbf_bin'] )
				devZipFiles			+= Install( join(devZipPath, 'bin'),		lenv['sbf_bin'] )
			if 'sbf_lib_object' in lenv:
				runtimeZipFiles		+= Install( join(runtimeZipPath, 'bin'),	lenv['sbf_lib_object'] )
				portableZipFiles	+= Install( join(portableZipPath, 'bin'),	lenv['sbf_lib_object'] )
				devZipFiles			+= Install( join(devZipPath, 'lib'),		lenv['sbf_lib_object'] )
			if 'sbf_bin_debuginfo' in lenv:
				devZipFiles			+= Install( join(devZipPath, 'pdb'),		lenv['sbf_bin_debuginfo'] )
			if 'sbf_lib_debuginfo' in lenv:
				devZipFiles			+= Install( join(devZipPath, 'pdb'),		lenv['sbf_lib_debuginfo'] )

			# Processes the 'stdlibs' project option
			for stdlib in lenv.get( 'stdlibs', [] ):
				filename = splitext(stdlib)[0] + env['SHLIBSUFFIX']
				pathFilename = searchFileInDirectories( filename, sbf.myLibInstallExtPaths )
				if pathFilename:
#					print("Found standard library %s" % pathFilename)
					depsZipFiles		+= Install( join(depsZipPath, 'bin'), pathFilename )
					portableZipFiles	+= Install( join(portableZipPath, 'bin'), pathFilename )
				else:
					print("Standard library %s not found (see 'stdlibs' project option of %s)." % (filename, projectName) )

			# Processes the share directory
			for file in lenv.get('sbf_share', []):
				sourceFile = join(projectPathName, file)
				runtimeZipFiles += InstallAs(	file.replace('share', runtimeDestPath, 1), sourceFile )
				portableZipFiles+= InstallAs(	file.replace('share', portableDestPath, 1), sourceFile )

			# Processes the built share directory
			for fileAbs in lenv.get('sbf_shareBuilt', []):
				fileRel = fileAbs[ fileAbs.index('share') : ]
				runtimeZipFiles += InstallAs(	fileRel.replace('share', runtimeDestPath, 1), fileAbs )
				portableZipFiles+= InstallAs(	fileRel.replace('share', portableDestPath, 1), fileAbs )

			# Processes the info files.
			for file in lenv.get('sbf_info', []):
				runtimeZipFiles += Install( runtimeDestPath, file )
				portableZipFiles += Install( portableDestPath, file )

			# Adds include files to dev zip
			for file in lenv.get('sbf_include', []):
				devZipFiles += InstallAs( join(devZipPath, file), join(projectPathName, file) )

			# Adds source files to src zip
			if lenv['vcsUse'] == 'yes':
				allFiles = sbf.myVcs.getAllVersionedFiles( projectPathName )

				projectRelPath = convertPathAbsToRel( rootOfProjects, projectPathName )

				for absFile in allFiles:
					relFile = convertPathAbsToRel( projectPathName, absFile )
					srcZipFiles += InstallAs( join(srcZipPath, projectRelPath, relFile), absFile )
			# else nothing to do

		#
		# Processes external dependencies
		#

		sbfRcNsisPath = join(env.sbf.mySCONS_BUILD_FRAMEWORK, 'rc', 'nsis' )

		# For each external dependency, do
		listOfExternalDependencies = sbf.getAllUses( sbf.getRootProjectEnv() )
		for useNameVersion in listOfExternalDependencies:
			# Extracts name and version of incoming external dependency
			useName, useVersion = splitUsesName( useNameVersion )
	#print ("%s = %s, %s" %(useNameVersion, useName, useVersion))

			# Retrieves use object for incoming dependency
			use = UseRepository.getUse( useName )
			if use:
				# Retrieves LIBS of incoming dependency
				libs = use.getLIBS( useVersion )
				if libs and len(libs) == 2:
					# Computes the search path list where libraries could be located
					searchPathList = sbf.myLibInstallExtPaths[:]
					libpath = use.getLIBPATH( useVersion )
					if libpath and (len(libpath) == 2):
						searchPathList.extend( libpath[1] )

					# For each library, do
					for file in libs[1]:
						filename = file + env['SHLIBSUFFIX']
						pathFilename = searchFileInDirectories( filename, searchPathList )
						if pathFilename:
#							print ("Found library %s" % pathFilename)
							depsZipFiles		+= Install( join(depsZipPath, 'bin'), pathFilename )
							portableZipFiles	+= Install( join(portableZipPath, 'bin'), pathFilename )
						else:
							raise SCons.Errors.UserError( "File %s not found." % filename )
				else:
					raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s." % (useNameVersion, sbf.myPlatform) )


				# Retrieves license file(s) of incoming dependency from IUse class
				warningAboutLicense = True
				licenses = use.getLicenses( useVersion )
				if licenses is not None:
					if len(licenses)>0:
						for filename in licenses:
							pathFilename = searchFileInDirectories( filename, licenseInstallExtPaths )
							if pathFilename:
								#print ("Found license %s" % pathFilename)
								warningAboutLicense = False
								depsZipFiles		+= Install( join(depsZipPath, 'license'), pathFilename )
								portableZipFiles	+= Install( join(portableZipPath, 'license'), pathFilename )
							else:
								raise SCons.Errors.UserError( "File %s not found." % filename )
					else:
						warningAboutLicense = False
				# else: warningAboutLicense = True


				# Retrieves license file(s) of incoming dependency using implicit license file(s) if any

				# license file without prefix (case: only one license file)
				licenses = ['license.{0}{1}.txt'.format( useName, useVersion)]
				# license file with prefix (case: several license files)
				for prefix in range(9):
					licenses += ['{0}license.{1}{2}.txt'.format( prefix, useName, useVersion)]
				for filename in licenses:
					pathFilename = searchFileInDirectories( filename, licenseInstallExtPaths )
					if pathFilename:
#						print ("Found license %s" % pathFilename)
						warningAboutLicense = False
						depsZipFiles		+= Install( join(depsZipPath, 'license'), pathFilename )
						portableZipFiles	+= Install( join(portableZipPath, 'license'), pathFilename )
					#else nothing to do

				# Prints warning if needed
				if warningAboutLicense:
					print ('sbfWarning: No license file for {0}'.format(useNameVersion))


				# Retrieves redistributables of incoming dependency
				for redistributable in use.getRedist( useVersion ):
					if not isinstance(redistributable, tuple) and isExtractionSupported(redistributable):
						if not env.GetOption('clean'):
							# @todo deferred extraction
							print ( 'Extracts {redist} into {destination}'.format(redist=redistributable, destination=portableZipPath) )
							extractArchive( join(sbfRcNsisPath, 'Redistributable', redistributable), portableZipPath )
							print ( 'Extracts {redist} into {destination}'.format(redist=redistributable, destination=depsZipPath) )
							extractArchive( join(sbfRcNsisPath, 'Redistributable', redistributable), depsZipPath )

		runtimeZip = runtimeZipPath + env['SEVENZIPSUFFIX']
		Alias( 'zipRuntime_generate7z', env.SevenZipAdd( runtimeZip, Dir(runtimeZipPath) ) )
		Alias( 'zipruntime',	[runtimeZipFiles, 'zipRuntime_generate7z'] )

		depsZip = depsZipPath + env['SEVENZIPSUFFIX']
		Alias( 'zipDeps_generate7z', env.SevenZipAdd( depsZip, Dir(depsZipPath) ) )
		Alias( 'zipdeps',		[depsZipFiles, 'zipDeps_generate7z'] )

		Alias( 'portable', portableZipFiles )

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
			env.createRsyncAction( os.path.basename(runtimeZip), File(runtimeZip), 'zipruntime' )
			env.createRsyncAction( os.path.basename(depsZip), File(depsZip), 'zipdeps' )
			env.createRsyncAction( '', Dir(portableZipPath), 'portable' )
			env.createRsyncAction( os.path.basename(portableZip), File(portableZip), 'zipportable' )
			env.createRsyncAction( os.path.basename(devZip), File(devZip), 'zipdev' )

			if len(srcZipFiles) > 0:
				env.createRsyncAction( os.path.basename(srcZip), File(srcZip), 'zipsrc' )
			#else: nothing to do

		Alias( 'zip', ['zipruntime', 'zipdeps', 'zipportable', 'zipdev', 'zipsrc'] )

		### nsis target ###
		Alias( 'nsis', ['infofile', 'build', portableZipFiles] ) # @todo uses 'zipportable' and @todo check order 'build', 'infofile'

		# Copies redistributable related files
		sbfNSISPath = join(env.sbf.mySCONS_BUILD_FRAMEWORK, 'NSIS' )
		Alias( 'nsis', env.Install( zipPakPath, join(sbfNSISPath, 'redistributable.nsi') ) )
		Alias( 'nsis', env.Install( zipPakPath, join(sbfRcNsisPath, 'redistributableDatabase.nsi') ) )

		# @todo Creates a function to InstallAs( dirDest, dirSrc * )
		redistributableFiles = []
		searchFiles( join(sbfRcNsisPath, 'Redistributable'), redistributableFiles, ['.svn'] )

		installRedistributableFiles = []
		for file in redistributableFiles :
			installRedistributableFiles += env.InstallAs( join( zipPakPath, file.replace(sbfRcNsisPath + os.sep, '') ), file )
		# endtodo
		Alias( 'nsis', installRedistributableFiles )

		# Generates several nsis files
		nsisRedistFiles		= [ join( zipPakPath, rootProjectEnv['sbf_project'] + '_install_redist.nsi' ), join( zipPakPath, rootProjectEnv['sbf_project'] + '_uninstall_redist.nsi' ) ]
		nsisInstallFiles	= join( zipPakPath, rootProjectEnv['sbf_project'] + '_install_files.nsi' )
		nsisUninstallFile	= join( zipPakPath, rootProjectEnv['sbf_project'] + '_uninstall_files.nsi' )

		Alias( 'nsis', rootProjectEnv.Command( nsisRedistFiles, portableZipPath, rootProjectEnv.Action( redistGeneration, printRedistGeneration ) ) )
		#AlwaysBuild( nsisRedistFiles )
		Alias( 'nsis', env.Command( nsisInstallFiles, portableZipPath, env.Action( zipPrinterForNSISInstallFiles, printZipPrinterForNSISInstallFiles ) ) )
		#AlwaysBuild( nsisInstallFiles )
		Alias( 'nsis', env.Command( nsisUninstallFile, portableZipPath, env.Action( zipPrinterForNSISUninstallFiles, printZipPrinterForNSISUninstallFiles ) ) )
		#AlwaysBuild( nsisUninstallFile )

		# Main nsis file
		Alias( 'nsis', rootProjectEnv.Command( portableZipPath + '.nsi', [nsisRedistFiles, nsisInstallFiles, nsisUninstallFile], rootProjectEnv.Action( nsisGeneration, printNsisGeneration ) ) )
		AlwaysBuild( portableZipPath + '.nsi' )

# @todo Nsis builder
		nsisRootPath = locateProgram( 'nsis' )
		nsisSetupFile = '{project}_{version}{config}_{date}_setup.exe'.format(project=env.sbf.myProject, version=env.sbf.myVersion, config=env.sbf.my_PostfixLinkedToMyConfig, date=env.sbf.myDate)

		nsisBuildAction = env.Command(	join(zipPakPath, nsisSetupFile), portableZipPath + '.nsi',
										"\"{0}\" $SOURCES".format( join(nsisRootPath, 'makensis.exe' ) ) )
		AlwaysBuild( nsisBuildAction )
		Alias( 'nsis', nsisBuildAction )

		# clean and mrproper targets
		Alias( ['zip_clean', 'zip_mrproper'], 'zip' )
		Clean( ['zip_clean', 'zip_mrproper'], zipPakPath )
		Alias( ['nsis_clean', 'nsis_mrproper'], 'nsis' )
		Clean( ['nsis_clean', 'nsis_mrproper'], zipPakPath )

		if env['publishOn'] :
			# @todo print message
			env.createRsyncAction( nsisSetupFile, File(join(zipPakPath, nsisSetupFile)), 'nsis' )
		# @todo uses zip2exe on win32 ?
