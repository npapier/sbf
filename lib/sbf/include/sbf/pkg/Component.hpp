#ifndef _SBF_PKG_COMPONENT_HPP_
#define _SBF_PKG_COMPONENT_HPP_

#include <string>

#include <boost/filesystem/path.hpp>
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
 * @brief	Base class for components of the system of packages and modules.
 */
struct SBF_API Component
{
	/**
	 * @name	Properties
	 */
	//@{
	const std::string & getName() const;					///< Retrieves the name of the package.
	const std::string & getVersion() const;					///< Retrieves the version of the package.
	const std::string getNameAndVersion() const;			///< Retrieves the name and version string of the package.
	const boost::shared_ptr< Package > getParent() const;	///< Retrieves the parent package (returns null if none).
	virtual const boost::filesystem::path getPath( const PathType & type ) const = 0;	///< Retrieves the path owned by the component for the given type.
	const boost::filesystem::path getPathSafe( const PathType & type ) const;			///< Retrieves the path owned by the component for the given type and ensures that the path exists.
	//@}

protected:

	const std::string					m_name;		///< The package name.
	const std::string					m_version;	///< The package version.
	const boost::weak_ptr< Package >	m_parent;	///< The package parent.

	/**
	 * @brief	Constructor
	 */
	Component(
		const std::string & name,
		const std::string & version,
		const boost::weak_ptr< Package > parent = boost::weak_ptr< Package >() );
};


} // namespace pkg

} // namespace sbf


#endif // _SBF_PKG_COMPONENT_HPP_