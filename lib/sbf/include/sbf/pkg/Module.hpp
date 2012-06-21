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
#include "sbf/pkg/Component.hpp"
#include "sbf/pkg/types.hpp"


namespace sbf
{

namespace pkg
{


struct Package;


/**
 * @brief	Allows to manage dynamically loadable modules.
 */
struct SBF_API Module : public Component
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
	const std::string getInfoFromFile() const;								///< Loads defailed informations from file.
	const boost::filesystem::path getPath( const PathType & type ) const;	///< Retrieves the path owned by the component for the given type.
	const bool hasInfoFile() const;											///< Tells if the module has detailed information file.
	//@}

protected:

	/**
	 * @brief	Constructor
	 */
	Module( const boost::weak_ptr< Package > parent, const std::string & name, const std::string & version );
};


} // namespace pkg

} // namespace sbf


#endif // _SBF_PKG_MODULE_HPP_
