// SConsBuildFramework - Copyright (C) 2011, 2012, Guillaume Brocker, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker
// Author Nicolas Papier

#include "sbf/operations.hpp"

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

} // namespace sbf
