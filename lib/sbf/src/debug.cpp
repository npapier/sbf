// SConsBuildFramework - Copyright (C) 2011, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Nicolas Papier

#include "sbf/debug.hpp"

#ifdef _WIN32
 #include <windows.h>
 #include <dbghelp.h> // MINIDUMP_EXCEPTION_INFORMATION
#endif

#include <iostream>



namespace
{

#ifdef _WIN32
LONG WINAPI toplevelExceptionFilter( struct _EXCEPTION_POINTERS *exceptionInfo )
{
	std::cerr << "Top level exception interception: Generate dump...\n" << std::endl;
	sbf::generateMiniDump(exceptionInfo);
	return EXCEPTION_EXECUTE_HANDLER;
}
#endif

}



namespace sbf
{


#ifdef _WIN32

void installToplevelExceptionHandler()
{
	SetUnhandledExceptionFilter(&toplevelExceptionFilter);
}


int generateMiniDump( void * input )
{
	EXCEPTION_POINTERS* pExceptionPointers = (EXCEPTION_POINTERS*) input;

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
												//MiniDumpNormal,
												MiniDumpWithDataSegs,
												//MiniDumpWithFullMemory,
												&exceptionParam,
												NULL, NULL);

	// Closes mini-dump file
	CloseHandle( hDumpFile );

	//
	return EXCEPTION_EXECUTE_HANDLER;
}

#else
int generateMiniDump( void * input )
{
	assert( false && "Not yet implemented" );
}

#endif

} // namespace sbf

