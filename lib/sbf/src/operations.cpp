// SConsBuildFramework - Copyright (C) 2011, 2012, 2013, Guillaume Brocker, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker
// Author Nicolas Papier

#include "sbf/operations.hpp"


#ifdef _WIN32
  #include <windows.h>
#endif // _WIN32


namespace sbf
{


#define STRINGIFY(x) #x
#define TOSTRING(x) STRINGIFY(x)


const std::string getPlatform()
{
	#ifdef SBF_PLATFORM
		return TOSTRING(SBF_PLATFORM);
	#else
		#error "Undefined SBF platform";
	#endif
}


const std::string getCC()
{
	#ifdef SBF_CC
		return TOSTRING(SBF_CC);
	#else
		#error "Undefined SBF CC";
	#endif
}


const double getCCVersionNumber()
{
	#ifdef SBF_CC_VERSION_NUMBER
		return SBF_CC_VERSION_NUMBER;
	#else
		#error "Undefined SBF cc version number";
	#endif
}


const std::string getCCVersion()
{
	#ifdef SBF_CC_VERSION
		return TOSTRING(SBF_CC_VERSION);
	#else
		#error "Undefined SBF cc version";
	#endif
}


const std::string getPlatformCCPostfix()
{
	#ifdef SBF_PLATFORM_CC_VERSION
		return TOSTRING(SBF_PLATFORM_CC_VERSION);
	#else
		#error "Undefined SBF platform and cc postfix";
	#endif
}


const std::string getConfigurationPostfix()
{
#ifdef _DEBUG
	return std::string("_D");
#else
	return std::string("");
#endif
}


const boost::filesystem::path getRootPath()
{
#ifdef WIN32
	char pathFilename[1024*4];

	const DWORD length = GetModuleFileName( 0, pathFilename, sizeof(pathFilename) );
	if ( length < sizeof(pathFilename) )
	{
		return boost::filesystem::path(pathFilename).parent_path().parent_path();
	}
	else
	{
		return boost::filesystem::path();
	}
#else
	#warning "Not yet implemented"
	assert(false);
	return boost::filesystem::path();
#endif
}



} // namespace sbf
