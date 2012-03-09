// SConsBuildFramework - Copyright (C) 2012, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker

#ifndef _SBF_MODULE_PACKAGE_HPP_
#define _SBF_MODULE_PACKAGE_HPP_

#include <string>
#include <vector>
#include <boost/enable_shared_from_this.hpp>
#include <boost/filesystem.hpp>
#include <boost/shared_ptr.hpp>

#include "sbf/sbf.hpp"
#include "sbf/pkg/types.hpp"


namespace sbf
{

namespace pkg
{


struct Module;
struct Pluggable;


/**
 * @brief	Provide package system management and package interactions.
 */
struct SBF_API Package : public boost::enable_shared_from_this< Package >
{
	/**
	 * @name	Containers and iterators
	 */
	//@{
	typedef std::vector< boost::shared_ptr< Package > >	PackageContainer;
	typedef PackageContainer::const_iterator			const_iterator;

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
	static const_iterator begin();					///< Retrieves the iterator on the beginning of the package collection.
	static boost::shared_ptr< Package > current();	///< Retrieves the package representing the running programm.
	static const_iterator end();					///< Retrieves the iterator on the end of the package collection.
	//@}

	/**
	 * @name	Properties
	 */
	//@{
	const std::string & getName() const;										///< Retrieves the name of the package.
	const std::string & getVersion() const;										///< Retrieves the version of the package.
	const boost::filesystem::path & getPath() const;							///< Retrieves the root directory of the package.
	const boost::filesystem::path getPath( const PathType & type ) const;		///< Retrieves the given path in the package tree.
	const boost::filesystem::path getPathSafe( const PathType & type ) const;	///< Retrieves the given path in the package tree and also ensures that the path exists.
	//@}

	/**
	 * @name	Modules
	 */
	//@{
	/**
	 * @brief	Retrieves the given module.
	 *
	 * If none of the registered module matches the query, then a new module instance will created and returned.
	 * So you have to be carefull because the given name and version may not match a real module of the system.
	 *
	 * @param	name	a module name
	 * @param	version	a optionnal module version, if not specified the first matching module will be returned.
	 *
	 * @return	a shared pointer to the module
	 */
	const boost::shared_ptr< Module > getModule( const std::string & name, const std::string & version = std::string() ) const;
	
	/** 
	 * @brief	Retrieves the iterator on the module collection's beginning.
	 */
	module_iterator moduleBegin();

	/** 
	 * @brief	Retrieves the iterator on the module collection's beginning.
	 */
	const_module_iterator moduleBegin() const;

	/**
	 * @brief	Retrieves how many modules have identified and registered.
	 */
	const unsigned int moduleCount() const;

	/**
	 * @brief	Retrieves the iterator on the module collection's end.
	 */
	module_iterator moduleEnd();

	/**
	 * @brief	Retrieves the iterator on the module collection's end.
	 */
	const_module_iterator moduleEnd() const;
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
	const boost::shared_ptr< Pluggable > findPluggable( const std::string & name, const std::string & version = std::string() ) const;
	
	/**
	 * @brief	Gets plugable module list having the given tag.
	 */
	const std::vector< std::string > getPlugablesByTag( const std::string & tag ) const;

	/**
	 * @brief	Loads plugable modules having the given tag
	 */
	void loadPlugablesByTag( const std::string & tag );

	/** 
	 * @brief	Retrieves the iterator on the module collection's beginning.
	 */
	pluggable_iterator pluggableBegin();

	/** 
	 * @brief	Retrieves the iterator on the pluggable collection's beginning.
	 */
	const_pluggable_iterator pluggableBegin() const;

	/**
	 * @brief	Retrieves how many pluggables have identified and registered.
	 */
	const unsigned int pluggableCount() const;

	/**
	 * @brief	Retrieves the iterator on the pluggable collection's end.
	 */
	pluggable_iterator pluggableEnd();

	/**
	 * @brief	Retrieves the iterator on the pluggable collection's end.
	 */
	const_pluggable_iterator pluggableEnd() const;
	//@}
	

private:

	static PackageContainer		m_packages;	///< The collection of packages found on the system.

	const std::string				m_name;			///< The package name.
	const std::string				m_version;		///< The package version.
	const boost::filesystem::path	m_path;			///< The package root's path.
	mutable ModuleContainer			m_modules;		///< The collection of modules available in the package.
	PluggableContainer				m_pluggables;	///< The collection of pluggable modules available in the package (references modules stored in m_modules).

	/**
	 * @brief	Constructor
	 */
	Package( const std::string & name, const std::string & version, const boost::filesystem::path & root );

	/** 
	 * @name	Helpers
	 */
	//@{
	static void init();		///< Initializes the whole system.
	void initPluggables();	///< Initializes the pluggable modules of the package.
	//@}
};

} // namespace pkg

} // namespace sbf


#endif // _SBF_PKG_PACKAGE_HPP_
