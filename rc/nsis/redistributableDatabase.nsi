### Redistributable\Codec ###
!define TSCC				"codec_tscc.exe"
;MessageBox MB_YESNO "Install Windows video codec for viewing TechSmith-encoded videos ?" /SD IDYES IDNO endTscc

!define ENSHARPENDECODER	"codec_ensharpendecoder_win.exe"
; MessageBox MB_YESNO "Install Windows video codec for viewing Ensharpen-encoded videos ?" /SD IDYES IDNO endEnsharpendecoder

### Redistributable\VCPP ###
# CLVERSION_DEPENDENCY
!define VCPP2005SP1		"Microsoft Visual C++ 2005 SP1 Redistributable Package (x86)_vcredist_x86.exe"
!define VCPP2008SP1		"Microsoft Visual C++ 2008 SP1 Redistributable Package (x86)_vcredist_x86.exe"
!define VCPP2010		"Microsoft Visual C++ 2010 Redistributable Package (x86)_vcredist_x86.exe"
!define VCPP2012_32		"Microsoft Visual C++ 2012 Redistributable Package (x86)_vcredist_x86.exe"
!define VCPP2012_64		"Microsoft Visual C++ 2012 Redistributable Package (x64)_vcredist_x64.exe"
!define VCPP2013_32		"Microsoft Visual C++ 2013 Redistributable Package (x86)_vcredist_x86.exe"
!define VCPP2013_64		"Microsoft Visual C++ 2013 Redistributable Package (x64)_vcredist_x64.exe"

!define CL80			"${VCPP2005SP1}"
!define CL80EXP			"${CL80}"
!define CL90			"${VCPP2008SP1}"
!define CL90EXP			"${CL90}"
!define CL100			"${VCPP2010}"
!define CL100EXP		"${CL100}"
!define CL110			"${VCPP2012_32}"
!define CL110EXP		"${CL110}"
!define CL120			"${VCPP2013_32}"
!define CL120EXP		"${CL120}"
; MessageBox MB_YESNO "Install Microsoft Visual C++ 2005 SP1 Redistributable Package (x86) ?" /SD IDYES IDNO endVCPP2005SP1
