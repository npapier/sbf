// SConsBuildFramework - Copyright (C) 2012, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker

#ifndef _SBF_PKG_PLUGGABLE_HPP_
#define _SBF_PKG_PLUGGABLE_HPP_

#include "sbf/pkg/Module.hpp"


namespace sbf
{

namespace pkg
{


/**
 * @brief	Implements modules that can be plugged while application is running.
 */
struct Pluggable : public Module
{
	friend struct Package;

	struct DynLib;	///< Provides an abstraction of the low level system binary dynamic library.
	
	/**
	 * @brief	Tells if the given module is loaded.
	 */
	SBF_API const bool isLoaded() const;
	
	/**
	 * @brief	Tells if the given module has an unloading function.
	 */
	SBF_API bool hasUnloadingFunction();

	/**
	 * @brief	Tells if the given module can be unloaded.
	 */
	SBF_API bool canBeUnloaded();

	/**
	 * @brief	Stops the given module from being unloaded.
	 */
	SBF_API void blockUnloading();

	/**
	 * @brief	Loads the module, if not already loaded.
	 */
	SBF_API void load();

	/**
	 * @brief	Unloads the module.
	 */
	SBF_API void unload();

private:

	boost::shared_ptr< DynLib >	m_library;			///< References the low level binary library.
	bool						m_canBeUnloaded;	///< Tells if the module can't be unloaded.

	/**
	 * @brief	Constructor
	 */
	Pluggable( 
		const std::string & name,
		const std::string & version,
		const boost::filesystem::path & rootPath,
		boost::weak_ptr< Package > parent );
};


} // namespace pkg

} // namespace sbf

#endif // _SBF_PKG_PLUGGABLE_HPP_
