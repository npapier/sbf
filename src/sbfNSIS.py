# SConsBuildFramework - Copyright (C) 2009, 2010, 2011, 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from os.path import join, splitext

from src.sbfArchives import extractArchive, isExtractionSupported
from src.sbfFiles	import *
from src.sbfRsync import createRsyncAction
from src.sbfSevenZip import create7ZipCompressAction
from src.sbfTools	import locateProgram
from src.sbfUses	import UseRepository
from src.sbfUtils	import capitalize
from src.sbfUI		import askQuestion
from src.sbfVersion import splitUsesName, splitDeploymentPrecond
from src.SConsBuildFramework import stringFormatter, nopAction
from SCons.Script import *


# @todo debug zipsrc if a used file is no more under vcs.
# @todo Improves redist macros (adding message and with/without confirmation)
# @todo improves output



### Helpers ####

def installAs( lenv, dirDest, dirSource, pruneDirectoriesPatterns = ['.svn'] ):
	"""Copy the directory tree from dirSource in dirDest using lenv.InstallAs(). pruneDirectoriesPatterns is used to exclude several sources directories."""
	files = []
	searchFiles( dirSource, files, pruneDirectoriesPatterns )

	installFiles = []
	parentOfDirSource = os.path.dirname(dirSource)
	for file in files:
		installFiles += lenv.InstallAs( file.replace(parentOfDirSource, dirDest, 1), file )
	return installFiles



def printNSISGeneration( target, source, env ):
	return stringFormatter(env, 'Generating {0} nsis setup program'.format(env['sbf_project']))

### project_redist.nsi and project_uninstall_redist.nsi generator ###
def printRedistGeneration( target, source, env ):
	return 'Generating {0} and {1} (redist files)'.format(os.path.basename(str(target[0])), os.path.basename(str(target[1])))

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



### project_install_files.nsi generator ###
def printGenerateNSISInstallFiles( target, source, env ):
	targetName = str(target[0])
	sourceName = str(source[0])
	return 'Generating {0} (nsis install files) from {1}'.format(os.path.basename(targetName), sourceName)

def generateNSISInstallFiles( target, source, env ):
	# Retrieves informations
	targetName = str( target[0] )
	sourceName = str( source[0] )

	encounteredFiles		= []
	encounteredDirectories	= []
	searchAllFilesAndDirectories( sourceName, encounteredFiles, encounteredDirectories )

	# Creates target file
	with open( targetName, 'w' ) as outputFile:
		# Creates directories
		for directory in encounteredDirectories:
			outputFile.write( 'CreateDirectory \"$OUTDIR\{0}\"\n'.format(convertPathAbsToRel(sourceName, directory)) )

		# Copies files
		for file in encounteredFiles:
			outputFile.write( 'File \"/oname=$OUTDIR\{0}\" \"{1}\"\n'.format(convertPathAbsToRel(sourceName, file), file) )


### project_uninstall_files.nsi generator ###
def printGenerateNSISUninstallFiles( target, source, env ):
	targetName = str(target[0])
	sourceName = str(source[0])
	return 'Generating {0} (nsis uninstall files) from {1}'.format(os.path.basename(targetName), sourceName)

def generateNSISUninstallFiles( target, source, env ):
	# Retrieves informations
	targetName = str( target[0] )
	sourceName = str( source[0] )

	encounteredFiles		= []
	encounteredDirectories	= []
	searchAllFilesAndDirectories( sourceName, encounteredFiles, encounteredDirectories, walkTopDown = False )

	# Creates target file
	with open( targetName, 'w' ) as outputFile:
		# Removes files
		for file in encounteredFiles:
			outputFile.write( 'Delete \"$INSTDIR\{0}\"\n'.format(convertPathAbsToRel(sourceName, file)) )

		# Removes directories
		for directory in encounteredDirectories:
			outputFile.write( 'RmDir \"$INSTDIR\{0}\"\n'.format(convertPathAbsToRel(sourceName, directory)) )


### project.nsi generator ###
def printGenerateNSISMainScript( target, source, env ):
	targetName = str(target[0])
	return ( 'Generating {0} (nsis main script)'.format(os.path.basename(targetName)) )


def __computeICON( lenv ):
	iconFile = os.path.join( lenv['sbf_projectPathName'], 'rc', lenv['sbf_project']+'.ico')
	if os.path.exists( iconFile ):
		return 'Icon "{0}"'.format( iconFile )


def generateNSISMainScript( target, source, env ):
	# Retrieves/computes additional information
	targetName = str(target[0])
	sbf = env.sbf

	# Open output file
	with open( targetName, 'w' ) as file:
		# Retrieves informations (all executables, ...)
		rootProject = env['sbf_project']

		mainProject = ''
		products	= []
		executables	= []
		for (projectName, lenv) in env.sbf.myParsedProjects.iteritems():
			if lenv['type'] == 'exec':
				#print lenv['sbf_project'], os.path.basename(lenv['sbf_bin'][0])
				if len(products) == 0:
					mainProject = lenv['sbf_project']
				products.append( lenv['productName'] + sbf.my_PostfixLinkedToMyConfig )
				executables.append( os.path.basename(lenv['sbf_bin'][0]) )

		# Generates PRODUCTNAME
		PRODUCTNAME = ''
		for (i, product) in enumerate(products):
			PRODUCTNAME += "!define PRODUCTNAME{0}	\"{1}\"\n".format(i, product)

		# Generates PRODUCTEXE, SHORTCUT, DESKTOPSHORTCUT, QUICKLAUNCHSHORTCUT, UNINSTALL_SHORTCUT, UNINSTALL_DESKTOPSHORTCUT and UNINSTALL_QUICKLAUNCHSHORTCUT
		PRODUCTEXE						= ''
		SHORTCUT						= ''
		DESKTOPSHORTCUT					= ''
		QUICKLAUNCHSHORTCUT				= ''
		UNINSTALL_SHORTCUT				= ''
		UNINSTALL_DESKTOPSHORTCUT		= ''
		UNINSTALL_QUICKLAUNCHSHORTCUT	= ''
#		if len(executables) > 1:
#			SHORTCUT = '  CreateDirectory \"${STARTMENUROOT}\\tools\"\n'
#			UNINSTALL_SHORTCUT	=	'  Delete \"${STARTMENUROOT}\\tools\\*.*\"\n'
#			UNINSTALL_SHORTCUT	+=	'  RMDir \"${STARTMENUROOT}\\tools\"\n'

		for (i, executable) in enumerate(executables) :
			PRODUCTEXE	+=	'!define PRODUCTEXE{0}	"{1}"\n'.format( i, executable)
			if i > 0:
				SHORTCUT	+=	'  SetOutPath \"$INSTDIR\\bin\"\n'
				SHORTCUT	+=	"  CreateShortCut \"${STARTMENUROOT}\\tools\\${PRODUCTNAME%s}.lnk\" \"$INSTDIR\\bin\\${PRODUCTEXE%s}\" \"\" \"$INSTDIR\\bin\\${PRODUCTEXE%s}\" 0\n" % (i, i, i)
			else:
				SHORTCUT						=	'  SetOutPath \"$INSTDIR\\bin\"\n'
				SHORTCUT						+=	'  CreateShortCut \"${STARTMENUROOT}\\${PRODUCTNAME0}.lnk\" \"$INSTDIR\\bin\\${PRODUCTEXE0}\" \"\" \"$INSTDIR\\bin\\${PRODUCTEXE0}\" 0\n'
				DESKTOPSHORTCUT					=	'  SetOutPath \"$INSTDIR\\bin\"\n'
				DESKTOPSHORTCUT					+=	'  CreateShortCut \"$DESKTOP\\${PRODUCTNAME0}.lnk\" \"$INSTDIR\\bin\\${PRODUCTEXE0}\" \"\" \"$INSTDIR\\bin\\${PRODUCTEXE0}\" 0\n'
				QUICKLAUNCHSHORTCUT				=	'  SetOutPath \"$INSTDIR\\bin\"\n'
				QUICKLAUNCHSHORTCUT				+=	'  CreateShortCut \"$QUICKLAUNCH\\${PRODUCTNAME0}.lnk\" \"$INSTDIR\\bin\\${PRODUCTEXE0}\" \"\" \"$INSTDIR\\bin\\${PRODUCTEXE0}\" 0\n'
				UNINSTALL_DESKTOPSHORTCUT		=	'  Delete \"$DESKTOP\\${PRODUCTNAME0}.lnk\"\n'
				UNINSTALL_QUICKLAUNCHSHORTCUT	=	'  Delete \"$QUICKLAUNCH\\${PRODUCTNAME0}.lnk\"\n'

		PRODUCTEXE += "!define PRODUCTEXE	${PRODUCTEXE0}\n"

		# installationDirectorySection and onInitInstallationDirectory
		if env['deploymentType'] in ['none', 'standalone']:
			### standalone|none project
			embedded_deploymentType = ''
			installationDirectorySection = """
; standalone or none project
InstallDir "$PROGRAMFILES\${SBFPROJECTVENDOR}\${SBFPRODUCTNAME}${SBFPROJECTCONFIG}\${SBFPROJECTVERSION}"

; Registry key to check for directory (so if you install again, it will overwrite the old one automatically)
InstallDirRegKey HKLM "${REGKEYROOT}" "Install_Dir"
"""
			onInitInstallationDirectory = '; standalone/none project initializes the installation directory in global section and not here.'
		else:
			### embedded project
			assert( env['deploymentType'] == 'embedded' )

			embedded_deploymentType = '!define EMBEDDED_DEPLOYMENTTYPE'

			if len(env['deploymentPrecond'])==0:
				print ('sbfError: deploymentPrecond have to be defined for {0} project.'.format(env['sbf_project']))
				Exit(1)

			# Extract deployment preconditions
			(name, operator, version) = splitDeploymentPrecond(env['deploymentPrecond'])

			# Test version
			assert( operator == '>=' )

			testVersionPrecond = """
			; prepare version numbers
			${{VersionConvert}} $1 "" $5
			${{VersionConvert}} ${{DEPLOYMENTPRECOND_STANDALONE_VERSION}} "" $6
			;MessageBox MB_OK "$1 >= ${{DEPLOYMENTPRECOND_STANDALONE_VERSION}} => $5 >= $6"				; debug

			; test version
			${{VersionCompare}} $5 $6 $7

			;MessageBox MB_OK "VersionCompare=$7"														; debug

			; >=
			${{If}} $7 == 2
				; test failed (<)
				MessageBox MB_ICONSTOP|MB_OK "Version of ${{DEPLOYMENTPRECOND_STANDALONE_NAME}} currently installed in the system is $1. But it have to be at least ${{DEPLOYMENTPRECOND_STANDALONE_VERSION}}."
				Abort
			${{EndIf}}

			; test passed
""".format()

			installationDirectorySection = """
; embedded project

; deploymentPrecond = 'projectName >= 2-0-beta15'
!define DEPLOYMENTPRECOND_STANDALONE_NAME				"{deploymentPrecond_standalone_name}"
!define DEPLOYMENTPRECOND_STANDALONE_COMPAREOPERATOR	"{deploymentPrecond_standalone_compareOperator}"
!define DEPLOYMENTPRECOND_STANDALONE_VERSION			"{deploymentPrecond_standalone_version}"

Function initInstallDir

	ReadRegStr $0 HKLM "Software\${{SBFPROJECTVENDOR}}\${{DEPLOYMENTPRECOND_STANDALONE_NAME}}" "Install_Dir"
	ReadRegStr $1 HKLM "Software\${{SBFPROJECTVENDOR}}\${{DEPLOYMENTPRECOND_STANDALONE_NAME}}" "Version"

	; Test if standalone is installed
	${{If}} $0 == ''
		; never installed, abort
		MessageBox MB_ICONSTOP|MB_OK "${{DEPLOYMENTPRECOND_STANDALONE_NAME}} have to be installed in the system before installing '${{SBFPRODUCTNAME}}'."
		Abort
	${{Else}} ;$0 != ''
		${{If}} $1 == ''
			; already installed, but not now => abort
			MessageBox MB_ICONSTOP|MB_OK "${{DEPLOYMENTPRECOND_STANDALONE_NAME}} have to be installed in the system before installing '${{SBFPRODUCTNAME}}'."
			Abort
		${{Else}} ; $0 != '' & $1 != ''
			; debug message
			MessageBox MB_OK "${{DEPLOYMENTPRECOND_STANDALONE_NAME}} v$1 is installed in the system in $0."

			; test version precondition
			{testVersionPrecond}

			StrCpy $INSTDIR "$0\packages\${{SBFPROJECTNAME}}_${{SBFPROJECTVERSION}}"

			; debug message
			MessageBox MB_OK "Installing ${{SBFPRODUCTNAME}} in $INSTDIR"
		${{EndIf}}
	${{EndIf}}
FunctionEnd
""".format( deploymentPrecond_standalone_name=name, deploymentPrecond_standalone_compareOperator=operator, deploymentPrecond_standalone_version=version, testVersionPrecond = testVersionPrecond )

			onInitInstallationDirectory = ' ; Initialize $INSTDIR\n Call initInstallDir'

		# Generates ICON
		# icon from the project launching sbf ?
		ICON = __computeICON( sbf.myParsedProjects[rootProject] )
		# icon from the first project containing an executable ?
		if not ICON and mainProject:
			ICON = __computeICON( sbf.myParsedProjects[mainProject] )

		# no icon ?
		if not ICON:
			ICON = "; no icon"


		str_sbfNSISTemplate = """\
; sbfNSISTemplate.nsi
;
; This script :
; - It will install files into a "PROGRAMFILES\SBFPROJECTVENDOR\SBFPROJECTNAME SBFPROJECTCONFIG\SBFPROJECTVERSION" or a directory that the user selects for 'standalone' or 'none' project
; - or in a directory found in registry for 'embedded' project
; - checks if deploymentPrecond is true (for embedded project) @TODO all operators
; - remember the installation directory (so if you install again, it will overwrite the old one automatically) and version.
; - creates a 'var' directory with full access for 'Users' and backups 'var' directory if already present.
; - icon of setup program comes from the launching project (if it contains an icon in rc/project.ico), otherwise from the first executable project (if any and if it contains an icon), else no icon at all.
; - ProductName, CompanyName, LegalCopyright, FileDescription, FileVersion and ProductVersion fields in the version tab of the File Properties are filled.
; - install in registry Software/SBFPROJECTVENDOR/SBFPROJECTNAME/Version
; - run as admin and installation occurs for all users
; - components chooser
; - has uninstall support (no modify, no repair).
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
!include "LogicLib.nsh"
!include "WordFunc.nsh"


SetCompressor lzma
XPStyle on

!define SBFPROJECTNAME				"{projectName}"
!define SBFPRODUCTNAME				"{productName}"
!define SBFPROJECTVERSION			"{projectVersion}"
!define SBFPROJECTCONFIG			"{projectConfig}"
!define SBFPROJECTVENDOR			"{projectVendor}"
!define SBFDATE						"{date}"
{embedded_deploymentType}


; SETUPFILE
!define SETUPFILE "${{SBFPRODUCTNAME}}_${{SBFPROJECTVERSION}}${{SBFPROJECTCONFIG}}_${{SBFDATE}}_setup.exe"

;
!define REGKEYROOT		"Software\${{SBFPROJECTVENDOR}}\${{SBFPROJECTNAME}}"
!define STARTMENUROOT	"$SMPROGRAMS\${{SBFPROJECTVENDOR}}\${{SBFPRODUCTNAME}}"

; PRODUCTNAME section
{productNameSection}

; PRODUCTEXE
{productExe}

;--------------------------------
; The installation directory
{installationDirectorySection}

Function .onInit
 ; Abort installation process if installer is already running
 System::Call 'kernel32::CreateMutexA(i 0, i 0, t "${{SETUPFILE}}") i .r1 ?e'
 Pop $R0
 StrCmp $R0 0 +3
 MessageBox MB_OK|MB_ICONSTOP "The installer is already running."
 Abort

 {onInitInstallationDirectory}
FunctionEnd

;--------------------------------

; The name of the installer
Name "${{SBFPRODUCTNAME}}${{SBFPROJECTCONFIG}} v${{SBFPROJECTVERSION}}"

; Version information
VIAddVersionKey "ProductName" "${{SBFPRODUCTNAME}}"
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


; Request application privileges for Windows Vista
RequestExecutionLevel admin

;--------------------------------

; Pages

Page components

!ifndef EMBEDDED_DEPLOYMENTTYPE
 Page directory
!endif

Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

;--------------------------------

; The stuff to install
Section "${{SBFPRODUCTNAME}} core (required)"
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

  AccessControl::GrantOnFile "$INSTDIR\\var" "(S-1-5-32-545)" "FullAccess"
;AccessControl::EnableFileInheritance "$INSTDIR\\var"

  ; Redistributable
  !include "${{SBFPROJECTNAME}}_install_redist.nsi"

  ; Write the installation path into the registry
  WriteRegStr HKLM "${{REGKEYROOT}}" "Install_Dir" "$INSTDIR"

  ; Write the version into the registry
  WriteRegStr HKLM "${{REGKEYROOT}}" "Version" "${{SBFPROJECTVERSION}}"

  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${{SBFPROJECTNAME}}" "DisplayIcon" '"$INSTDIR\\bin\\${{PRODUCTEXE}}"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${{SBFPROJECTNAME}}" "DisplayName" "${{SBFPROJECTVENDOR}} ${{SBFPRODUCTNAME}} ${{SBFPROJECTVERSION}}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${{SBFPROJECTNAME}}" "DisplayVersion" "${{SBFPROJECTVERSION}}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${{SBFPROJECTNAME}}" "Publisher" "${{SBFPROJECTVENDOR}}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${{SBFPROJECTNAME}}" "UninstallString" '"$INSTDIR\\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${{SBFPROJECTNAME}}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${{SBFPROJECTNAME}}" "NoRepair" 1
  WriteUninstaller "uninstall.exe"

SectionEnd



!ifndef EMBEDDED_DEPLOYMENTTYPE
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
!endif


;--------------------------------
; Uninstaller

Section "Uninstall"

  SetShellVarContext all

  ; Remove files
  !include "${{SBFPROJECTNAME}}_uninstall_files.nsi"

  ; Remove redistributable
  !include "${{SBFPROJECTNAME}}_uninstall_redist.nsi"

  ; Remove registry keys
  ;DeleteRegKey HKLM "${{REGKEYROOT}}"			; containing 'Install_Dir' and 'Version'
  DeleteRegValue HKLM "${{REGKEYROOT}}" "Version"
  
  DeleteRegKey /ifempty HKLM "Software\${{SBFPROJECTVENDOR}}"

  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${{SBFPROJECTNAME}}"

  ; Remove uninstaller
  Delete $INSTDIR\uninstall.exe

  ; Remove installation directory
  RmDir $INSTDIR

  ; Remove shortcuts, if any
{removeStartMenuShortcuts}
  Delete "${{STARTMENUROOT}}\*.*"
  ; Remove directories used
  RMDir "${{STARTMENUROOT}}"
  ; Remove root directory if empty
  RMDir "$SMPROGRAMS\${{SBFPROJECTVENDOR}}"
 
  {removeDesktopShortcuts}
 
SectionEnd
""".format(	projectName=env['sbf_project'],
			productName=env['productName'],
			projectNameCapitalized=capitalize(env['sbf_project']),
			projectVersion=env['version'],
			projectConfig=env.sbf.my_PostfixLinkedToMyConfig,
			projectVendor=env.sbf.myCompanyName,
			projectDescription=env['description'],
			date=env.sbf.myDate,
			embedded_deploymentType=embedded_deploymentType,
			productNameSection=PRODUCTNAME,
			productExe=PRODUCTEXE,
			productVersion='{0}.{1}.{2}.0'.format( env['sbf_version_major'], env['sbf_version_minor'], env['sbf_version_maintenance'] ),
			installationDirectorySection=installationDirectorySection,
			onInitInstallationDirectory=onInitInstallationDirectory,
			icon=ICON,
			startMenuShortcuts=SHORTCUT,
			desktopShortcuts=DESKTOPSHORTCUT,
#			quicklaunchShortcuts=QUICKLAUNCHSHORTCUT,
			removeStartMenuShortcuts=UNINSTALL_SHORTCUT,
			removeDesktopShortcuts=UNINSTALL_DESKTOPSHORTCUT,
#			removeQuicklaunchShortcuts=UNINSTALL_QUICKLAUNCHSHORTCUT
			)

		file.write( str_sbfNSISTemplate )


def __printGenerateNSISSetupProgram( target, source, env ):
	targetName = str(target[0])
	return ( '\nBuilding {0} setup program'.format(env['sbf_project']) )



### special zip related targets : zipRuntime, zipDeps, portable, zipPortable, zipDev, zipSrc and zip ###
# @todo zip*_[build,install,clean,mrproper]
# @todo zip doxygen

### ZIP/NSIS ###
def getTmpNSISPath( lenv ):
	sbf = lenv.sbf
	return join( sbf.myBuildPath, 'nsis' )

def __getProjectSubdir( lenv ):
	sbf = lenv.sbf
	return lenv['sbf_project'] + '_' + lenv['version'] + sbf.my_Platform_myCCVersion + sbf.my_FullPostfix

def getTmpNSISPortablePath( lenv ):
	return join( getTmpNSISPath(lenv), __getProjectSubdir(lenv) + '_portable_' + lenv.sbf.myDate )

def getTmpNSISSetupPath( lenv ):
	return join( getTmpNSISPath(lenv), __getProjectSubdir(lenv) + '_setup_' + lenv.sbf.myDate )

def initializeNSISInstallDirectories( sbf, lenv ):
	sbf.myNSISInstallDirectories = []

	if len( set(['portable', 'zipportable', 'nsis']) & sbf.myBuildTargets )>0:			# @todo set()
		# portable, zipportable
		portablePath = getTmpNSISPortablePath(lenv)
		varPortablePath = join( portablePath, 'var' )
		# To ensure that only latest files would be package in zip* and nsis targets, removes directories
		if not GetOption('weakPublishing'):
			Execute([Delete(varPortablePath), Delete(portablePath), Mkdir(portablePath), Mkdir(varPortablePath)])

			nsisSetupPath = getTmpNSISSetupPath(lenv)
			Execute([Delete(nsisSetupPath), Mkdir(nsisSetupPath)])
		else:
			print ('Weak publishing option is enabled. So intermediate files are not cleaned.\nTips: Do the first publishing of the day without --weak-publishing.\n')
		sbf.myNSISInstallDirectories.append( portablePath )
	#else nothing to do

	# for debugging
	#print 'myNSISInstallDirectories:', sbf.myNSISInstallDirectories


def __warnAboutProjectExclude( env ):
	# Checks project exclusion to warn user
	if env['exclude'] and len(env['projectExclude'])>0:
		answer = askQuestion(	"WARNING: The following projects are excluded from the build : {0}\nWould you continue the process".format(env['projectExclude']),
								['yes', 'no'], env['queryUser'] )
		if answer == 'n':		# @todo test != answer no, n, y, yes...
			raise SCons.Errors.UserError( "Build interrupted by user." )
		#else continue the build


# @todo zip targets => package targets
def configureZipAndNSISTargets( lenv ):
	sbf = lenv.sbf

# @todo others targets (deps and runtime at least)
	#zipAndNSISTargets = set( ['zipruntime', 'zipdeps', 'portable', 'zipportable', 'zipdev', 'zipsrc', 'zip', 'nsis'] )
	zipAndNSISTargets = set( ['portable', 'zipportable', 'nsis'] )

# @todo clean targets, test clean targets
	cleanAndMrproperTargets = set( ['zip_clean', 'zip_mrproper', 'nsis_clean', 'nsis_mrproper'] )
	allTargets = zipAndNSISTargets | cleanAndMrproperTargets

	# Have to enable clean/mrproper
	if	len(cleanAndMrproperTargets & sbf.myBuildTargets) > 0:
		lenv.SetOption('clean', 1)

	if len(allTargets & sbf.myBuildTargets) > 0:
		__warnAboutProjectExclude(lenv)

		# lazzy scons lenv construction => @todo generalize (but must be optional)

		# 'portable' target
		portablePath = getTmpNSISPortablePath(lenv)
		portableZipPath = portablePath + '.7z'
		Alias( 'portable', ['infofile', 'install', 'deps'] )

		# 'zipportable' target
		if 'zipportable' in sbf.myBuildTargets:
			Execute( Delete(portableZipPath) )
			Alias( 'zipportable', ['infofile', 'install', 'deps'] )
			create7ZipCompressAction( lenv, portableZipPath, portablePath, 'zipportable' )

		# 'nsis' target
		if 'nsis' in sbf.myBuildTargets:
			tmpNSISSetupPath = getTmpNSISSetupPath(lenv)

			Alias( 'nsis', ['infofile', 'install', 'deps'] )

			# Copies redistributable related files (redistributable.nsi and redistributableDatabase.nsi)
			sbfNSISPath = join(sbf.mySCONS_BUILD_FRAMEWORK, 'NSIS' )
			installRedistributableFiles = lenv.Install( tmpNSISSetupPath, join(sbfNSISPath, 'redistributable.nsi') )

			sbfRcNsisPath = join(sbf.mySCONS_BUILD_FRAMEWORK, 'rc', 'nsis' )
			installRedistributableFiles += lenv.Install( tmpNSISSetupPath, join(sbfRcNsisPath, 'redistributableDatabase.nsi') )

			# Copies $SCONS_BUILD_FRAMEWORK/rc/nsis/Redistributable/*
			installRedistributableFiles += installAs( lenv, tmpNSISSetupPath, join(sbfRcNsisPath, 'Redistributable') )
			Alias( 'nsis', lenv.Command( 'dummy_nsis_print' + lenv['sbf_project'], 'dummy.in', Action(nopAction, printNSISGeneration) ) )
			Alias( 'nsis', installRedistributableFiles )

			# Generates several nsis files
			# project_install_redist.nsi and project_uninstall_redist.nsi
			nsisRedistFiles		= [ join( tmpNSISSetupPath, lenv['sbf_project'] + '_install_redist.nsi' ), join( tmpNSISSetupPath, lenv['sbf_project'] + '_uninstall_redist.nsi' ) ]
			Alias( 'nsis', lenv.Command( nsisRedistFiles, 'dummy.in', lenv.Action(redistGeneration, printRedistGeneration) ) )

			# project_install_files.nsi
			nsisInstallFiles	= join( tmpNSISSetupPath, lenv['sbf_project'] + '_install_files.nsi' )
			Alias( 'nsis', lenv.Command( nsisInstallFiles, portablePath, lenv.Action(generateNSISInstallFiles, printGenerateNSISInstallFiles) ) )

			# project_uninstall_files.nsi
			nsisUninstallFile	= join( tmpNSISSetupPath, lenv['sbf_project'] + '_uninstall_files.nsi' )
			Alias( 'nsis', lenv.Command( nsisUninstallFile, portablePath, lenv.Action(generateNSISUninstallFiles, printGenerateNSISUninstallFiles) ) )

			# Main nsis file
			nsisTargetFile = join(tmpNSISSetupPath, lenv['sbf_project']+'.nsi')
			sourceFiles = [nsisRedistFiles, nsisInstallFiles, nsisUninstallFile]

			Alias( 'nsis', lenv.Command( nsisTargetFile, sourceFiles, lenv.Action(generateNSISMainScript, printGenerateNSISMainScript) ) )

			# Build nsis project
			nsisLocation = locateProgram( 'nsis' )

			nsisSetupFile = '{project}_{version}{config}_{date}_setup.exe'.format(project=lenv['productName'], version=lenv['version'], config=sbf.my_PostfixLinkedToMyConfig, date=lenv.sbf.myDate)

			nsisBuildAction = lenv.Command(	join(tmpNSISSetupPath, nsisSetupFile), nsisTargetFile,
											"\"{0}\" $SOURCES".format(join(nsisLocation, 'makensis')) )
			Alias( 'nsis', lenv.Command('nsis_build.out', 'dummy.in', Action(nopAction, __printGenerateNSISSetupProgram) ) )
			Alias( 'nsis', nsisBuildAction )
			if lenv['publishOn']: createRsyncAction( lenv, '', join(tmpNSISSetupPath, nsisSetupFile), 'nsis' )

		if lenv['publishOn']:
			createRsyncAction( lenv, '', portablePath, 'portable' )
			createRsyncAction( lenv, '', portableZipPath, 'zipportable' )


