// SConsBuildFramework - Copyright (C) 2011, 2012, 2013, Guillaume Brocker, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker
// Author Nicolas Papier

#ifndef _SBF_OPERATIONS_HPP_
#define _SBF_OPERATIONS_HPP_

#include <boost/filesystem.hpp>
#include <string>

#include "sbf/sbf.hpp"

namespace sbf
{



/**
  * @brief Retrieves the current platform.
  *
  * @return the current platform (win32, cygwin, posix or darwin).
  */
SBF_API const std::string getPlatform();

/**
 * @brief Retrieves the compiler used for building.
 *
 * @return the compiler (cl, gcc).
 */
SBF_API const std::string getCC();


/**
 * @brief Retrieves the compiler version number used for building.
 *
 * @return the compiler version number (8.0 for MS/cl 8.0, 4.002001 for gcc 4.2.1).
 */
SBF_API const double getCCVersionNumber();


/**
 * @brief Retrieves the compiler version used for building.
 *
 * @return the compiler version (9-0, 4-2-1)
 */
SBF_API const std::string getCCVersion();


/**
 * @brief Retrieves the postfix added by sbf to executable and library filenames.
 *
 * @return the postfix containing platform and compiler version (_win32_cl9-0Exp, _posix_gcc4-2-1)
 */
SBF_API const std::string getPlatformCCPostfix();


/**
 * @brief Retrieves the postfix added by sbf to distinguish debug and release configuration.
 *
 * @return the postfix containing the configuration (on windows: _D in debug configuration or nothing in release configuration).
 */
SBF_API const std::string getConfigurationPostfix();

/**
 * @brief Retrieves the root path containing the sbf library
 *
 * @return path to the directory containing 'bin', 'share' and 'var' sub-directories or an empty() path.
 */
SBF_API const boost::filesystem::path getRootPath();


} // namespace sbf

#endif // _SBF_OPERATIONS_HPP_
