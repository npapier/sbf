// SConsBuildFramework - Copyright (C) 2009, Guillaume Brocker.
// Distributed under the terms of the GNU General Public License (GPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker

#ifndef _SFB_MODULES_HPP_
#define _SFB_MODULES_HPP_

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
struct Module
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
	SBF_API static ConstIterator begin();
	
	/**
	 * @brief	Retrieves the iterator on the registered module collection's end.
	 */
	SBF_API static ConstIterator end();
	
	/**
	 * @brief	Retrieves a registered module by its name or the current program or library if non name is specified.
	 */
	SBF_API static const Module & get( const std::string & name = MODULE_NAME );
	
	/**
	 * @brief	Retrieves the module for the current program fo library.
	 */
/*	static const Module & current()
	{
		return find( MODULE_NAME );
	}*/
	//@}
	
	/**
	 * @brief	Builds the module descriptor for the current program or library.
	 *
	 * Also registers the module into the global registry if not alreay done.
	 */
	Module()
	:	m_name( MODULE_NAME ),
		m_version( MODULE_VERSION )
	{
		const Module & found = get(m_name);
		
		assert( ! found && "A sbf::Module cannot get registered more than one time." );
		m_registry.push_back( this );
	}
	
	/**
	 * @brief	Destructor
	 */
	~Module()
	{
		Container::iterator	found = std::find(m_registry.begin(), m_registry.end(), this);

		if( found != m_registry.end() )
		{
			m_registry.erase( found );
		}
	}

	/**
	 * @name	Properties Access
	 */
	//@{
	/**
	 * @brief	Retrieves the name.
	 */
	const std::string getName() const
	{
		return m_name;
	}
	
	/**
	 * @brief	Retrieves the version.
	 */
	const std::string getVersion() const
	{
		return m_version;
	}

	/**
	 * @brief	Tells if the module descriptor is valid or not.
	 */
	operator const bool () const
	{
		return m_name.empty() == false && m_version.empty() == false;
	}
	//@}
	
	/**
	 * @name	Path Access
	 */
	//@{
	typedef enum
	{
		Share,	///< Path to shared resources.
		Var		///< Path to dynamic software data.
	} PathType;

	/**
	 * @brief	Converts a given path type into a string.
	 */
	SBF_API static const std::string toString( const PathType type );

	/**
	 * @brief	Retrieves the path of the given type for the given name and version.
	 *
	 * @param	type	defines the path type to retrieve
	 *
	 * @return	an absolute path, or empty if none.
	 */
	const boost::filesystem::path getPath( const PathType type ) const
	{
		assert( *this && "Cannot retrieve path for an invalid module");
		
		const boost::filesystem::path	namePath( m_name );
		const boost::filesystem::path	versionPath( m_version );
		boost::filesystem::path			basePath;
		
		basePath = boost::filesystem::system_complete( toString(type) );
		if( boost::filesystem::is_directory(basePath) )
		{
			return basePath / namePath / versionPath;
		}

		basePath = boost::filesystem::system_complete( boost::filesystem::path("..") / toString(type) );
		if( boost::filesystem::is_directory(basePath) )
		{
			return basePath / namePath / versionPath;
		}

		return boost::filesystem::path();
	}
	//@}
	
private:

	SBF_API static Container	m_registry;	///< Holds All registered modules.

	const std::string	m_name;		///< Holds the name string of a module.
	const std::string	m_version;	///< Holds the version string of a module.
	
	/**
	 * @brief	Unallowed copy constructor.
	 */
	Module( const Module & )
	{}
	
	/**
	 * @brief	Explicit constructor
	 */
	Module( const std::string & name, const std::string & version )
	:	m_name( name ),
		m_version( version )
	{}
};



} // namespace sbf



#endif // _SFB_MODULES_HPP_
