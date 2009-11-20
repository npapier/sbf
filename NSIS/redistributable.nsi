; SConsBuildFramework - Copyright (C) 2009, Nicolas Papier.
; Distributed under the terms of the GNU General Public License (GPL)
; as published by the Free Software Foundation.
; Author Nicolas Papier

; @todo MessageBox with custom text

; *** Low level macros ***

; Copy/Delete file
!macro InstallRedistributable file
	IfFileExists "$INSTDIR\Redistributable\*.*" +2
	CreateDirectory "$INSTDIR\Redistributable"
	File "/oname=$INSTDIR\Redistributable\${file}" "Redistributable\${file}"
!macroend

!macro RmRedistributable file
	Delete "$INSTDIR\Redistributable\${file}"
	RmDir "$INSTDIR\Redistributable"
!macroend


; Launch/UninstallString
!macro LaunchRedistributable file
	MessageBox MB_YESNO "Install ${file} ?" /SD IDYES IDNO +2
	ExecWait "$INSTDIR\Redistributable\${file}"
!macroend

; @todo Checks if $0  empty
!macro UninstallString name hklmPath
	ReadRegStr $0 HKLM "${hklmPath}" "UninstallString"
	MessageBox MB_YESNO "Uninstall ${name} ?" /SD IDYES IDNO +2
	ExecWait $0
!macroend


; MSILaunch/MSIUninstall
!macro MSILaunchRedistributableParams file params
	MessageBox MB_YESNO "Install ${file} ?" /SD IDYES IDNO +2
	ExecWait '"msiexec" ${params} "$INSTDIR\Redistributable\${file}"'
!macroend

!macro MSIUninstallRedistributable file
	MessageBox MB_YESNO "Uninstall ${file} ?" /SD IDYES IDNO +2
	ExecWait '"msiexec" /x "$INSTDIR\Redistributable\${file}"'
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


; *** High level macros ***
!macro InstallAndLaunchRedistributable file
	MessageBox MB_YESNO "Install ${file} ?" /SD IDYES IDNO +5
	IfFileExists "$INSTDIR\Redistributable\*.*" +2
	CreateDirectory "$INSTDIR\Redistributable"
	File "/oname=$INSTDIR\Redistributable\${file}" "Redistributable\${file}"
	ExecWait "$INSTDIR\Redistributable\${file}"
!macroend

!macro InstallAndMSILaunchRedistributableParams file params
	MessageBox MB_YESNO "Install ${file} ?" /SD IDYES IDNO +5
	IfFileExists "$INSTDIR\Redistributable\*.*" +2
	CreateDirectory "$INSTDIR\Redistributable"
	File "/oname=$INSTDIR\Redistributable\${file}" "Redistributable\${file}"
	ExecWait '"msiexec" ${params} "$INSTDIR\Redistributable\${file}"'
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
