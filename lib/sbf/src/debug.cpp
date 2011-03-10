// SConsBuildFramework - Copyright (C) 2011, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Nicolas Papier

#include "sbf/debug.hpp"

#ifdef _WIN32
 #include <windows.h>
 #include <dbghelp.h> // MINIDUMP_EXCEPTION_INFORMATION
#endif

#include <cassert>
#include <iostream>



namespace
{

#ifdef _WIN32
int generateMiniDump( void * input, MINIDUMP_TYPE miniDumpType )
{
	EXCEPTION_POINTERS* pExceptionPointers = (EXCEPTION_POINTERS*)input;

	// Creates mini-dump file
	HANDLE hDumpFile = CreateFile(	"core.dmp"/*szFileName*/,
									GENERIC_READ|GENERIC_WRITE,
									FILE_SHARE_WRITE|FILE_SHARE_READ,
									0, CREATE_ALWAYS, 0, 0);

	// Creates mini-dump
	MINIDUMP_EXCEPTION_INFORMATION exceptionParam;
	exceptionParam.ThreadId = GetCurrentThreadId();
	exceptionParam.ExceptionPointers = pExceptionPointers;
	exceptionParam.ClientPointers = TRUE;

	BOOL bMiniDumpSuccessful;
	bMiniDumpSuccessful = MiniDumpWriteDump(	GetCurrentProcess(), GetCurrentProcessId(),
												hDumpFile,
												miniDumpType,
												&exceptionParam,
												NULL, NULL);

	// Closes mini-dump file
	CloseHandle( hDumpFile );

	//
	return EXCEPTION_EXECUTE_HANDLER;
}

LONG WINAPI toplevelExceptionFilterCoreNormal( struct _EXCEPTION_POINTERS *exceptionInfo )
{
	std::cerr << "Top level exception interception: Generate dump..." << std::endl;

	MINIDUMP_TYPE minidumpType = (MINIDUMP_TYPE)(MiniDumpNormal);
	generateMiniDump(exceptionInfo, minidumpType);

	std::cerr << "Done" << std::endl;
	return EXCEPTION_EXECUTE_HANDLER;
}

LONG WINAPI toplevelExceptionFilterCoreFull( struct _EXCEPTION_POINTERS *exceptionInfo )
{
	std::cerr << "Top level exception interception: Generate dump..." << std::endl;

	MINIDUMP_TYPE minidumpType = (MINIDUMP_TYPE)(MiniDumpNormal | MiniDumpWithPrivateReadWriteMemory);
	generateMiniDump(exceptionInfo, minidumpType);

	std::cerr << "Done" << std::endl;
	return EXCEPTION_EXECUTE_HANDLER;
}

#else
int generateMiniDump( void * input, MINIDUMP_TYPE miniDumpType )
{
	assert( false && "Not yet implemented" );
}
#endif

}



namespace sbf
{


void installToplevelExceptionHandler( const CoreType coreType )
{
#ifdef _WIN32
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



} // namespace sbf
