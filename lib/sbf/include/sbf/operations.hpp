// SConsBuildFramework - Copyright (C) 2011, Guillaume Brocker.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker

#ifndef _SBF_OPERATIONS_HPP_
#define _SBF_OPERATIONS_HPP_

#include <string>

#include "sbf/sbf.hpp"

namespace sbf
{



/**
  * @brief	Retrieves the current platform.
  */
SBF_API const std::string getPlatform();

/**
 * @brief	Retrieves the compiler version used for building.
 */
SBF_API const std::string getCCVersion();



} // namespace sbf



#endif // _SBF_OPERATIONS_HPP_
 