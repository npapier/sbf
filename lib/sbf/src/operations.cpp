// SConsBuildFramework - Copyright (C) 2011, Guillaume Brocker.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker

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


const std::string getCCVersion()
{
	#ifdef SBF_CC_VERSION
		return TOSTRING(SBF_CC_VERSION);
	#else
		#error "Undefined SBF CC version";
	#endif
}


} // namespace sbf
