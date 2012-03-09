#include "sbf/pkg/types.hpp"

#include <cassert>


namespace sbf
{

namespace pkg
{


const std::string toString( const PathType & pathType )
{
	std::string	result;
	
	switch( pathType )
	{
	case BinPath:	result = "bin";   break;
	case VarPath:	result = "var";   break;
	case SharePath:	result = "share"; break;
	default:		assert( false && "Unsupported sbf::module::PathType" );
	}
	
	return result;
}


} // namespace pkg

} // namespace sbf
