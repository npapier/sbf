// SConsBuildFramework - Copyright (C) 2011, 2012, 2014, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Nicolas Papier
// Author Guillaume Brocker

#include "sbf/debug.hpp"

#ifdef _WIN32
 #include <windows.h>
 #include <DbgHelp.h> // MINIDUMP_EXCEPTION_INFORMATION and SymGetLineFromAddr64()
#endif

#include <cassert>
#include <iostream>
#include <sstream>



namespace
{

#ifdef _WIN32
// Retrieve the system error message for the last-error code
void handleLastError( const char *msg )
{
	DWORD errCode = GetLastError();

	if ( errCode != ERROR_SUCCESS )
	{
		char * err;
		if (!FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
						   NULL,
						   errCode,
						   MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), // default language
						   (LPTSTR) &err,
						   0,
						   NULL))
		{
			return;
		}
		else
		{
			printf( "ERROR: %s: %s\n", msg, err);
			LocalFree(err);
		}
	}
	// else nothing to do
}
#endif


#ifdef _WIN32

void toCerr( struct _EXCEPTION_POINTERS * exceptionInfo )
{
	const DWORD exceptionCode = exceptionInfo->ExceptionRecord->ExceptionCode;
	switch ( exceptionCode )
	{
		case EXCEPTION_ACCESS_VIOLATION:
			std::cerr << "EXCEPTION_ACCESS_VIOLATION" << std::endl;
			std::cerr << "The thread tried to read from or write to a virtual address for which it does not have the appropriate access." << std::endl;
			break;

		case EXCEPTION_ARRAY_BOUNDS_EXCEEDED:
			std::cerr << "EXCEPTION_ARRAY_BOUNDS_EXCEEDED" << std::endl;
			std::cerr << "The thread tried to access an array element that is out of bounds and the underlying hardware supports bounds checking." << std::endl;
			break;

		case EXCEPTION_BREAKPOINT:
			std::cerr << "EXCEPTION_BREAKPOINT" << std::endl;
			std::cerr << "A breakpoint was encountered." << std::endl;
			break;

		//default:
	}
}

static boost::filesystem::path	miniDumpDirectory;	///< Hold the path to the directory that will receive the mini dump file.

int generateMiniDump( void * input, MINIDUMP_TYPE miniDumpType )
{
	const boost::filesystem::path	filename				= miniDumpDirectory / "core.dmp";
	EXCEPTION_POINTERS				* pExceptionPointers	= (EXCEPTION_POINTERS*)input;

	// Creates mini-dump file
	HANDLE hDumpFile = CreateFile(	filename.string().c_str()/*szFileName*/,
									GENERIC_READ|GENERIC_WRITE,
									FILE_SHARE_WRITE|FILE_SHARE_READ,
									0, CREATE_ALWAYS, 0, 0);

	// Creates mini-dump
	MINIDUMP_EXCEPTION_INFORMATION exceptionParam;
	exceptionParam.ThreadId = GetCurrentThreadId();
	exceptionParam.ExceptionPointers = pExceptionPointers;
	exceptionParam.ClientPointers = TRUE;

	// @todo dynamic loading of Dbghelp
	HMODULE m_hDbhHelp = LoadLibrary( "dbghelp.dll" );
	if (m_hDbhHelp == NULL) return EXCEPTION_EXECUTE_HANDLER;

	BOOL bMiniDumpSuccessful;
	typedef BOOL (__stdcall *tMiniDumpWriteDump)(
				  _In_  HANDLE hProcess, _In_  DWORD ProcessId,
				  _In_  HANDLE hFile, _In_  MINIDUMP_TYPE DumpType,
				  _In_  PMINIDUMP_EXCEPTION_INFORMATION ExceptionParam, _In_  PMINIDUMP_USER_STREAM_INFORMATION UserStreamParam,
				  _In_  PMINIDUMP_CALLBACK_INFORMATION CallbackParam );
	tMiniDumpWriteDump pMiniDumpWriteDump = (tMiniDumpWriteDump) GetProcAddress(m_hDbhHelp, "MiniDumpWriteDump" );

	//bMiniDumpSuccessful = MiniDumpWriteDump(	GetCurrentProcess(), GetCurrentProcessId(),
	bMiniDumpSuccessful = pMiniDumpWriteDump(	GetCurrentProcess(), GetCurrentProcessId(),
												hDumpFile,
												miniDumpType,
												&exceptionParam,
												NULL, NULL);

	FreeLibrary(m_hDbhHelp);

	// Closes mini-dump file
	CloseHandle( hDumpFile );


	//
	return EXCEPTION_EXECUTE_HANDLER;
}

LONG WINAPI toplevelExceptionFilterCoreNormal( struct _EXCEPTION_POINTERS * exceptionInfo )
{
	std::cerr << "Top level exception interception: Generate dump..." << std::endl;
	toCerr( exceptionInfo );

	MINIDUMP_TYPE minidumpType = (MINIDUMP_TYPE)(MiniDumpNormal);
	generateMiniDump(exceptionInfo, minidumpType);

	std::cerr << "Done" << std::endl;
	return EXCEPTION_EXECUTE_HANDLER;
}

LONG WINAPI toplevelExceptionFilterCoreFull( struct _EXCEPTION_POINTERS * exceptionInfo )
{
	std::cerr << "Top level exception interception: Generate dump..." << std::endl;
	toCerr( exceptionInfo );

	MINIDUMP_TYPE minidumpType = (MINIDUMP_TYPE)(MiniDumpNormal | MiniDumpWithPrivateReadWriteMemory);
	generateMiniDump(exceptionInfo, minidumpType);

	std::cerr << "Done" << std::endl;
	return EXCEPTION_EXECUTE_HANDLER;
}

#else
	// Nothing to do.
#endif

}



namespace sbf
{


void installToplevelExceptionHandler( const CoreType coreType, const boost::filesystem::path & dumpDirectory )
{
#ifdef _WIN32
	miniDumpDirectory = dumpDirectory;

	switch ( coreType )
	{
		case CoreFull:
			SetUnhandledExceptionFilter(&toplevelExceptionFilterCoreFull);
			break;

		case CoreNormal:
			SetUnhandledExceptionFilter(&toplevelExceptionFilterCoreNormal);
			break;
		default:
			SetUnhandledExceptionFilter(&toplevelExceptionFilterCoreNormal);
			assert( false && "Unexpected CoreType value" );
	}
#else
	#warning "installToplevelExceptionHandler: Not yet implemented on non win32 platform"
#endif
}



#ifdef _WIN32

void printStackTrace()
{
	const int maxNumFrames = 64 * 1;
	void * stack[ maxNumFrames ];

	// SymInitialize()
	typedef BOOL (__stdcall *tSI)( IN HANDLE hProcess, IN PSTR UserSearchPath, IN BOOL fInvadeProcess );
	tSI pSI;

	// SymSetOptions()
	typedef DWORD (__stdcall *tSSO)( IN DWORD SymOptions );
	tSSO pSSO;

	// SymFromAddr()
	typedef BOOL (__stdcall *tSFA)(_In_ HANDLE hProcess, _In_ DWORD64 Address, _Out_opt_ PDWORD64 Displacement, _Inout_ PSYMBOL_INFO Symbol );
	tSFA pSFA;

	// SymGetLineFromAddr64()
	typedef BOOL (__stdcall *tSGLFA)( IN HANDLE hProcess, IN DWORD64 dwAddr, OUT PDWORD pdwDisplacement, OUT PIMAGEHLP_LINE64 Line );
	tSGLFA pSGLFA;

	// SymCleanup()
	typedef BOOL (__stdcall *tSC)( IN HANDLE hProcess );
	tSC pSC;

	HMODULE m_hDbhHelp = LoadLibrary( "dbghelp.dll" );
	if (m_hDbhHelp == NULL)
		return;

	pSI = (tSI) GetProcAddress(m_hDbhHelp, "SymInitialize" );

	pSSO = (tSSO) GetProcAddress(m_hDbhHelp, "SymSetOptions" );
	pSFA = (tSFA) GetProcAddress(m_hDbhHelp, "SymFromAddr" );
	pSGLFA = (tSGLFA) GetProcAddress(m_hDbhHelp, "SymGetLineFromAddr64" );

	pSC = (tSC) GetProcAddress(m_hDbhHelp, "SymCleanup" );

	//SymSetOptions( SYMOPT_LOAD_LINES | SYMOPT_UNDNAME | SYMOPT_DEFERRED_LOADS ); 
	pSSO( SYMOPT_LOAD_LINES | SYMOPT_UNDNAME | SYMOPT_DEFERRED_LOADS ); 

	const HANDLE process = GetCurrentProcess();

	//if (!SymInitialize( process, NULL, TRUE ) )
	if (!pSI( process, NULL, TRUE ) )
	{
		// SymInitialize failed
		handleLastError("SymInitialize returned error");
		return;
	}

	unsigned short frames	= CaptureStackBackTrace( 0, maxNumFrames, stack, NULL );
	SYMBOL_INFO  * symbol   = ( SYMBOL_INFO * )calloc( sizeof( SYMBOL_INFO ) + 256 * sizeof( char ), 1 );
	symbol->MaxNameLen   	= 255;
	symbol->SizeOfStruct 	= sizeof( SYMBOL_INFO );

	for( unsigned int i = 0; i < frames; i++ )
	{
		//SymFromAddr( process, ( DWORD64 )( stack[ i ] ), 0, symbol );
		pSFA( process, ( DWORD64 )( stack[ i ] ), 0, symbol );
		DWORD  dwDisplacement;
		IMAGEHLP_LINE64 line;

		line.SizeOfStruct = sizeof(IMAGEHLP_LINE64);
		if (	!strstr(symbol->Name,"VSDebugLib::") &&
				//SymGetLineFromAddr64(process, ( DWORD64 )( stack[ i ] ), &dwDisplacement, &line))
				pSGLFA(process, ( DWORD64 )( stack[ i ] ), &dwDisplacement, &line))
		{
				std::stringstream ss;
				ss << "function: " << symbol->Name << " - line: " << line.LineNumber << "\n";
				std::cerr << ss.str();
		}
		if (0 == strcmp(symbol->Name,"main")) break;
	}

	free( symbol );
	pSC( process );
	FreeLibrary(m_hDbhHelp);
}
#else
	#pragma message( "printStack() not defined in non WIN32 platform." )
	// http://stackoverflow.com/questions/77005/how-to-generate-a-stacktrace-when-my-gcc-c-app-crashes
void printStackTrace()
{}
#endif


} // namespace sbf
