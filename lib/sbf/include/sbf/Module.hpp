// SConsBuildFramework - Copyright (C) 2009, Guillaume Brocker and Nicolas Papier.
// Distributed under the terms of the GNU General Public License (GPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker and Nicolas Papier

#ifndef _SFB_MODULES_HPP_
#define _SFB_MODULES_HPP_

#pragma warning (push)
#pragma warning (disable: 4251)

#include <algorithm>
#include <cassert>
#include <vector>
#include <string>

#include <boost/filesystem.hpp>

#include "sbf/sbf.hpp"



namespace sbf
{



/**
 * @brief	Implements a module descriptor.
 *
 * A module represents either an executable file or a dynamically loaded library.
 */
struct SBF_API Module
{
	/**
	 * @name	Registered Modules Access
	 */
	//@{
	typedef std::vector< const Module * >	Container;
	typedef Container::const_iterator		ConstIterator;
	
	/**
	 * @brief	Retrieves the iterator on the registered module collection's begin.
	 */
	static ConstIterator begin();

	/**
	 * @brief	Retrieves the iterator on the registered module collection's end.
	 */
	static ConstIterator end();

	/**
	 * @brief	Retrieves a registered module by its name or the current program or library if non name is specified.
	 */
	static const Module & get( const std::string & name = MODULE_NAME );
	//@}

	/**
	 * @brief	Constructor
	 *
	 * By default, this constructs the module for the current program or library.
	 * Also registers the module into the global registry if not alreay done.
	 */
	Module( const std::string & name = MODULE_NAME, const std::string & version = MODULE_VERSION );

	/**
	 * @brief	Destructor
	 */
	~Module();

	/**
	 * @name	Properties Access
	 */
	//@{
	/**
	 * @brief	Retrieves the name.
	 */
	const std::string getName() const;

	/**
	 * @brief	Retrieves the version.
	 */
	const std::string getVersion() const;

	/**
	 * @brief	Tells if the module descriptor is valid or not.
	 */
	operator const bool () const;
	//@}


private:

	static Container	m_registry;	///< Holds All registered modules.
	const std::string	m_name;		///< Holds the name string of a module.
	const std::string	m_version;	///< Holds the version string of a module.

	/**
	 * @brief	Unallowed copy constructor.
	 */
	Module( const Module & )
	{}
};



} // namespace sbf


#pragma warning (pop)

#endif // _SFB_MODULES_HPP_
