; SConsBuildFramework - Copyright (C) 2009, 2010, Nicolas Papier.
; Distributed under the terms of the GNU General Public License (GPL)
; as published by the Free Software Foundation.
; Author Nicolas Papier

; @todo Enable/disable MessageBox with custom text

; *** Low level macros ***

; ** Copy/Delete file **
; Copy redist file in INSTDIR/Redistributable
!macro InstallRedistributable file
	IfFileExists "$INSTDIR\Redistributable\*.*" +2
	CreateDirectory "$INSTDIR\Redistributable"
	File "/oname=$INSTDIR\Redistributable\${file}" "Redistributable\${file}"
!macroend

; Delete redist file in INSTDIR/Redistributable
!macro RmRedistributable file
	Delete "$INSTDIR\Redistributable\${file}"
	RmDir "$INSTDIR\Redistributable"
!macroend


; ** Launch/UninstallString **
; Launch redist file with given parameters
!macro LaunchRedistributable file parameters
	MessageBox MB_YESNO "Install ${file} ?" /SD IDYES IDNO +2
	ExecWait "$INSTDIR\Redistributable\${file} ${parameters}"
!macroend

; Launch redist file with given parameters
!macro LaunchRedistributableQ file parameters
	ExecWait "$INSTDIR\Redistributable\${file} ${parameters}"
!macroend

; @todo Checks if $0 is empty
!macro UninstallString name hklmPath
	ReadRegStr $0 HKLM "${hklmPath}" "UninstallString"
	MessageBox MB_YESNO "Uninstall ${name} ?" /SD IDYES IDNO +2
	ExecWait $0
!macroend


; ** MSI launch and uninstall **

; Launch msiexec on file with given parameters
!macro MSILaunchRedistributable file parameters
	MessageBox MB_YESNO "Install ${file} ?" /SD IDYES IDNO +2
	ExecWait '"msiexec" ${parameters} "$INSTDIR\Redistributable\${file}"'
!macroend

; Launch msiexec on file with given parameters
!macro MSILaunchRedistributableQ file parameters
	ExecWait '"msiexec" ${parameters} "$INSTDIR\Redistributable\${file}"'
!macroend

; Launch uninstallation using msiexec on file with given parameters
!macro MSIUninstallRedistributable file parameters
	MessageBox MB_YESNO "Uninstall ${file} ?" /SD IDYES IDNO +2
	ExecWait '"msiexec" /x ${parameters} "$INSTDIR\Redistributable\${file}"'
!macroend


; unzip
!macro UnzipRedistributable file extractionDirectory
	MessageBox MB_YESNO "Unzip ${file} ?" /SD IDYES IDNO +5
	nsisunz::UnzipToLog "$INSTDIR\Redistributable\${file}" "${extractionDirectory}"
	; Always check result on stack
	Pop $0
	StrCmp $0 "success" +2
	DetailPrint "$0" ;print error message to log
!macroend

!macro UnzipRedistributableQ file extractionDirectory
	nsisunz::UnzipToLog "$INSTDIR\Redistributable\${file}" "${extractionDirectory}"
	; Always check result on stack
	Pop $0
	StrCmp $0 "success" +2
	DetailPrint "$0" ;print error message to log
!macroend


; *** High level macros ***
!macro InstallAndLaunchRedistributable file parameters
	MessageBox MB_YESNO "Install ${file} ?" /SD IDYES IDNO +5
	IfFileExists "$INSTDIR\Redistributable\*.*" +2
	CreateDirectory "$INSTDIR\Redistributable"
	File "/oname=$INSTDIR\Redistributable\${file}" "Redistributable\${file}"
	ExecWait "$INSTDIR\Redistributable\${file} ${parameters}"
!macroend

!macro InstallAndLaunchRedistributableQ file parameters
	!insertmacro InstallRedistributable "${file}"
	!insertmacro LaunchRedistributableQ "${file}" "${parameters}"
!macroend


!macro InstallAndMSILaunchRedistributable file parameters
	MessageBox MB_YESNO "Install ${file} ?" /SD IDYES IDNO +5
	IfFileExists "$INSTDIR\Redistributable\*.*" +2
	CreateDirectory "$INSTDIR\Redistributable"
	File "/oname=$INSTDIR\Redistributable\${file}" "Redistributable\${file}"
	!insertmacro MSILaunchRedistributableQ "${file}" "${parameters}"
!macroend

!macro InstallAndMSILaunchRedistributableQ file parameters
	!insertmacro InstallRedistributable "${file}"
	!insertmacro MSILaunchRedistributableQ "${file}" "${parameters}"
!macroend


!macro InstallAndUnzipRedistributable file extractionDirectory
	MessageBox MB_YESNO "Install ${file} ?" /SD IDYES IDNO +8
	IfFileExists "$INSTDIR\Redistributable\*.*" +2
	CreateDirectory "$INSTDIR\Redistributable"
	File "/oname=$INSTDIR\Redistributable\${file}" "Redistributable\${file}"
	nsisunz::UnzipToLog "$INSTDIR\Redistributable\${file}" "${extractionDirectory}"
	; Always check result on stack
	Pop $0
	StrCmp $0 "success" +2
	DetailPrint "$0" ;print error message to log
!macroend

!macro InstallAndUnzipRedistributableQ file extractionDirectory
	IfFileExists "$INSTDIR\Redistributable\*.*" +2
	CreateDirectory "$INSTDIR\Redistributable"
	File "/oname=$INSTDIR\Redistributable\${file}" "Redistributable\${file}"
	nsisunz::UnzipToLog "$INSTDIR\Redistributable\${file}" "${extractionDirectory}"
	; Always check result on stack
	Pop $0
	StrCmp $0 "success" +2
	DetailPrint "$0" ;print error message to log
!macroend
