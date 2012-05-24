// SConsBuildFramework - Copyright (C) 2012, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker

#ifndef _SBF_PKG_MODULE_HPP_
#define _SBF_PKG_MODULE_HPP_

#include <string>
#include <vector>
#include <boost/filesystem.hpp>
#include <boost/scoped_ptr.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/weak_ptr.hpp>

#include "sbf/sbf.hpp"
#include "sbf/pkg/types.hpp"


namespace sbf
{

namespace pkg
{


struct Package;


/**
 * @brief	Allows to manage dynamically loadable modules.
 */
struct SBF_API Module
{
	friend struct Package;

	/**
	 * @brief	Retrieves the module corresponding to the given name and version.
	 *
	 * By default, this method retrieves the module corresponding to the caller.
	 *
	 * @return	a module, null if none
	 */
	static boost::shared_ptr< Module > get( const std::string & name = MODULE_NAME, const std::string & version = MODULE_VERSION );

	/**
	 * @brief	Destructor
	 */
	virtual ~Module();
	
	/**
	 * @name	State and meta data
	 */
	//@{
	/**
	 * @brief	Retrieves the module name.
	 */
	const std::string & getName() const;

	/**
	 * @brief	Retrieves the name and version string of the module.
	 */
	const std::string getNameAndVersion() const;

	/**
	 * @brief	Retrieves the package owing the module.
	 */
	boost::shared_ptr< Package > getPackage() const;

	/**
	 * @brief	Retrieves the path owned by the module for the given type.
	 */
	const boost::filesystem::path getPath( const PathType & type ) const;

	/**
	 * @brief	Retrieves the path owned by the module for the given type and ensures that the path exists.
	 */
	const boost::filesystem::path getPathSafe( const PathType & type ) const;

	/**
	 * @brief	Retrieves the module version.
	 */
	const std::string & getVersion() const;

	/**
	 * @brief	Loads defailed informations from file.
	 */
	const std::string getInfoFromFile() const;

	/**
	 * @brief	Tells if the module has detailed information file.
	 */
	const bool hasInfoFile() const;
	//@}

protected:

	const boost::weak_ptr< Package >	m_package;	///< References the packages the module belongs to.
	const std::string					m_name;		///< Holds the module's name.
	const std::string					m_version;	///< Holds the module's version.

	/**
	 * @brief	Constructor
	 */
	Module( const boost::weak_ptr< Package > package, const std::string & name, const std::string & version );
};


} // namespace pkg

} // namespace sbf


#endif // _SBF_PKG_MODULE_HPP_
