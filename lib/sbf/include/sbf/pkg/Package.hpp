// SConsBuildFramework - Copyright (C) 2012, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker

#ifndef _SBF_PKG_PACKAGE_HPP_
#define _SBF_PKG_PACKAGE_HPP_

#include <string>
#include <vector>
#include <boost/enable_shared_from_this.hpp>
#include <boost/filesystem.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/weak_ptr.hpp>
#include <boost/property_tree/ptree.hpp>

#include "sbf/sbf.hpp"
#include "sbf/pkg/types.hpp"
#include "sbf/pkg/Component.hpp"


namespace sbf
{

namespace pkg
{


struct Module;
struct Pluggable;


/**
 * @brief	Provide package system management and package interactions.
 */
struct Package : public boost::enable_shared_from_this< Package >, public Component
{
	/**
	 * @name	Containers and iterators
	 */
	//@{
	typedef std::vector< boost::shared_ptr< Package > >	PackageContainer;
	typedef PackageContainer::iterator			iterator;

	typedef std::vector< boost::shared_ptr< Module > >	ModuleContainer;
	typedef ModuleContainer::iterator					module_iterator;
	typedef ModuleContainer::const_iterator				const_module_iterator;

	typedef std::vector< boost::shared_ptr< Pluggable > >	PluggableContainer;
	typedef PluggableContainer::iterator					pluggable_iterator;
	typedef PluggableContainer::const_iterator				const_pluggable_iterator;
	//@}

	/**
	 * @name	Package collection
	 */
	//@{
	SBF_API static iterator begin();								///< Retrieves the iterator on the beginning of the package collection.
	SBF_API static const boost::shared_ptr< Package > current();	///< Retrieves the package representing the running programm.
	SBF_API static iterator end();									///< Retrieves the iterator on the end of the package collection.
	SBF_API static const PackageContainer findDuplicates();			///< Retrieves the first packages having the same name but a different version.
	//@}

	/**
	 * @name	Configuration
	 */
	//@{
	SBF_API const bool isEnabled() const;			///< Tells if the package is enabled.
	SBF_API void setEnabled( const bool enable );	///< Enables or disables the package (may need a software restart to take effect).
	SBF_API const bool willBeEnabled() const;		///< Tells if the package will be enabled after a software restart.
	//@}

	/**
	 * @name	Modules
	 */
	//@{
	/**
	 * @brief	Retrieves the given module.
	 *
	 * @param	name	a module name
	 * @param	version	a optionnal module version, if not specified the first matching module will be returned.
	 *
	 * @return	a shared pointer to the module
	 */
	SBF_API const boost::shared_ptr< Module > findModule( const std::string & name, const std::string & version = std::string() ) const;
	
	/** 
	 * @brief	Retrieves the iterator on the module collection's beginning.
	 */
	SBF_API module_iterator moduleBegin();

	/** 
	 * @brief	Retrieves the iterator on the module collection's beginning.
	 */
	SBF_API const_module_iterator moduleBegin() const;

	/**
	 * @brief	Retrieves how many modules have identified and registered.
	 */
	SBF_API const unsigned int moduleCount() const;

	/**
	 * @brief	Retrieves the iterator on the module collection's end.
	 */
	SBF_API module_iterator moduleEnd();

	/**
	 * @brief	Retrieves the iterator on the module collection's end.
	 */
	SBF_API const_module_iterator moduleEnd() const;
	//@}

	/**
	 * @name	Pluggables
	 */
	//@{
	/**
	 * @brief	Retrieves the given pluggable module.
	 *
	 * @param	name	a module name
	 * @param	version	a optionnal module version, if not specified the first matching module will be returned.
	 *
	 * @return	a shared pointer to the found pluggable module, null if none.
	 */
	SBF_API const boost::shared_ptr< Pluggable > findPluggable( const std::string & name, const std::string & version = std::string() ) const;
	
	/**
	 * @brief	Gets plugable module list having the given tag.
	 */
	SBF_API const std::vector< std::string > getPlugablesByTag( const std::string & tag ) const;

	/**
	 * @brief	Loads plugable modules having the given tag
	 */
	SBF_API void loadPlugablesByTag( const std::string & tag );

	/** 
	 * @brief	Retrieves the iterator on the module collection's beginning.
	 */
	SBF_API pluggable_iterator pluggableBegin();

	/** 
	 * @brief	Retrieves the iterator on the pluggable collection's beginning.
	 */
	SBF_API const_pluggable_iterator pluggableBegin() const;

	/**
	 * @brief	Retrieves how many pluggables have identified and registered.
	 */
	SBF_API const unsigned int pluggableCount() const;

	/**
	 * @brief	Retrieves the iterator on the pluggable collection's end.
	 */
	SBF_API pluggable_iterator pluggableEnd();

	/**
	 * @brief	Retrieves the iterator on the pluggable collection's end.
	 */
	SBF_API const_pluggable_iterator pluggableEnd() const;
	//@}


private:

	static PackageContainer		m_packages;		///< The collection of packages found on the system.

	const bool					m_enabled;		///< Tells if the package is enable.
	mutable ModuleContainer		m_modules;		///< The collection of modules available in the package.
	PluggableContainer			m_pluggables;	///< The collection of pluggable modules available in the package (references modules stored in m_modules).
	boost::property_tree::ptree	m_settings;		///< Holds settings for the package.
	
	/**
	 * @brief	Constructor
	 *
	 * @param	name		a string containing the name of the package
	 * @param	version		a string containing the version of the package
	 * @param	rootPath	a path to the root directory of the package
	 * @param	parent		an optional reference to the parent package (default is none)
	 */
	Package( 
		const std::string & name, 
		const std::string & version, 
		const boost::filesystem::path & rootPath, 
		const boost::weak_ptr< Package > parent = boost::weak_ptr< Package >() );

	/** 
	 * @name	Helpers
	 */
	//@{
	static void init();								///< Initializes the whole system.
	void initModules( const PathType & pathType );	///< Initializes modules and pluggable modules of the package, looking into the given path.
	const boost::shared_ptr< Module > initModule( const PathType & pathType, const std::string & name, const std::string & version );	///< Initializes a module using the given path type, module name and version.
	//@}
};

} // namespace pkg

} // namespace sbf


#endif // _SBF_PKG_PACKAGE_HPP_
