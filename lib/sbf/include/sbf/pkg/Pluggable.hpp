// SConsBuildFramework - Copyright (C) 2012, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker

#ifndef _SBF_PKG_PLUGGABLE_HPP_
#define _SBF_PKG_PLUGGABLE_HPP_

#include <boost/property_tree/ptree.hpp>

#include "sbf/pkg/Module.hpp"


namespace sbf
{

namespace pkg
{


/**
 * @brief	Implements modules that can be plugged while application is running.
 */
struct SBF_API Pluggable : public Module
{
	friend struct Package;

	struct DynLib;	///< Provides an abstraction of the low level system binary dynamic library.
	typedef std::vector< std::string >	TagContainer;

	/**
	 * @brief	Retrieves the module description text.
	 */
	const std::string getDescription() const;

	/**
	 * @brief	Retrieves the module label.
	 */
	const std::string getLabel() const;

	/**
	 * @brief	Retrieves the payload available in the module meta data.
	 *
	 * @param	name	a string containing the name of the payload to retreive
	 */
	const boost::property_tree::ptree getPayload( const std::string & name ) const;

	/**
	 * @brief	Retrieves the module tags.
	 */
	const TagContainer getTags() const;

	/**
	 * @brief	Retrieves the module tags in a string.
	 */
	const std::string getTagsString() const;

	/**
	 * @brief	Tells if the given module is loaded.
	 */
	const bool isLoaded() const;
	
	/**
	 * @brief	Tells if the module has the given tag.
	 */
	const bool hasTag( const std::string & tag ) const;

	/**
	 * @brief	Tells if the given module has an unloading function.
	 */
	bool hasUnloadingFunction();

	/**
	 * @brief	Tells if the given module can be unloaded.
	 */
	bool canBeUnloaded();

	/**
	 * @brief	Stops the given module from being unloaded.
	 */
	void blockUnloading();

	/**
	 * @brief	Loads the module, if not already loaded.
	 */
	void load();

	/**
	 * @brief	Unloads the module.
	 */
	void unload();

private:

	boost::property_tree::ptree	m_data;				///< Holds the module's meta data.
	boost::shared_ptr< DynLib >	m_library;			///< References the low level binary library.
	bool						m_canBeUnloaded;	///< Tells if the module can't be unloaded.

	/**
	 * @brief	Constructor
	 */
	Pluggable( boost::weak_ptr< Package > package, const std::string & name, const std::string & version );
};


} // namespace pkg

} // namespace sbf

#endif // _SBF_PKG_PLUGGABLE_HPP_
