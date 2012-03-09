#include "sbf/pkg/operations.hpp"

#include <vector>
#include <boost/shared_ptr.hpp>

#include "sbf/pkg/Module.hpp"
#include "sbf/pkg/Pluggable.hpp"


namespace sbf
{
	
namespace pkg
{
	
	
void loadAllPluggables()
{
	typedef std::vector< boost::shared_ptr< Pluggable > > Container;

	Container	pluggables;

	getAllPluggables( pluggables );
	for( Container::const_iterator pluggable = pluggables.begin(); pluggable != pluggables.end(); ++pluggable )
	{
		(*pluggable)->load();
	}
}


} // namespace pkg

} // namespace sbf
