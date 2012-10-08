#ifndef _SBF_PKG_COMPONENT_HPP_
#define _SBF_PKG_COMPONENT_HPP_

#include <string>

#include <boost/filesystem/path.hpp>
#include <boost/property_tree/ptree.hpp>
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
	typedef std::vector< std::string >	TagContainer;

	/**
	 * @name Properties
	 */
	//@{
	const std::string getDescription() const;		///< Retrieves the module description text.
	const std::string getLabel() const;				///< Retrieves the module label.
	const std::string & getName() const;			///< Retrieves the name of the package.
	const std::string getNameAndVersion() const;	///< Retrieves the name and version string of the package.
	const TagContainer getTags() const;				///< Retrieves the module tags.
	const std::string getTagsString() const;		///< Retrieves the module tags in a string.
	const boost::shared_ptr< Package > getParent() const;						///< Retrieves the parent package (returns null if none).
	const boost::filesystem::path getPath( const PathType & type ) const;		///< Retrieves the path owned by the component for the given type.
	const boost::filesystem::path getPathSafe( const PathType & type ) const;	///< Retrieves the path owned by the component for the given type and ensures that the path exists.
	const boost::filesystem::path getRootPath() const;	///< Retrieves the root path for the component.
	const std::string & getVersion() const;				///< Retrieves the version of the package.
	const bool hasTag( const std::string & tag ) const;	///< Tells if the module has the given tag.
	//@}

	/**
	 * @name Data access
	 */
	//@{
	const boost::property_tree::ptree getDataAsTree( const std::string & key ) const;	///< Retrieves a data tree for the given key.
	const std::string getDataAsString( const std::string & key ) const;					///< Retrieves a data string for the given key.
	void setData( const std::string & key, const std::string & value );					///< Set a string in the data for the given key.
	//@}

protected:

	const std::string					m_name;			///< The component's name.
	const std::string					m_version;		///< The component's version.
	const boost::filesystem::path		m_rootPath;		///< The component root's path.
	const boost::weak_ptr< Package >	m_parent;		///< The component's parent.
	const boost::property_tree::ptree	m_constData;	///< Holds the component's constant meta data.
	boost::property_tree::ptree			m_editableData;	///< Holds the component's editable meta data.

	/**
	 * @brief	Constructor
	 */
	Component(
		const std::string & name,
		const std::string & version,
		const boost::filesystem::path & rootPath,
		const boost::weak_ptr< Package > parent = boost::weak_ptr< Package >() );

	/**
	 * @name Helpers
	 */
	//@{
	void loadData();		///< Loads constant and editable data.
	void saveData() const;	///< Saves editable data.
	//@}
};


} // namespace pkg

} // namespace sbf


#endif // _SBF_PKG_COMPONENT_HPP_