// SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Nicolas Papier

#include <string>



namespace sbf
{

namespace simd
{

namespace detail
{



struct CPUInformations
{
	CPUInformations();

	/**
	 * @name Data
	 */
	//@{
	std::string		m_cpuString;

	int				m_nLogicalProcessors;
	bool			m_bMultithreading;

	bool			m_hasMMX;
	bool			m_hasSSE;
	bool			m_hasSSE2;
	bool			m_hasSSE3;
	bool			m_hasSSSE3;
	bool			m_hasSSE41;
	bool			m_hasSSE42;
	bool			m_hasFMA;
	bool			m_hasMOVBE;
	bool			m_hasAVX;
	//@}
};


const CPUInformations& getCPUInformations();


} // namespace detail

} // namespace simd

} // namespace sbf
