// SConsBuildFramework - Copyright (C) 2009, Guillaume Brocker.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker

#ifndef _SBF_SBF_HPP_
#define _SBF_SBF_HPP_


// #pragma warning (disable:4250 4251 4275 4996)


namespace sbf
{

#ifdef _WIN32
    #ifdef SBF_EXPORTS
        #define SBF_API __declspec(dllexport)
	#else
        #define SBF_API __declspec(dllimport)
    #endif
#else
    #define SBF_API
#endif

} // namespace sbf

#endif // _SBF_SBF_HPP_
