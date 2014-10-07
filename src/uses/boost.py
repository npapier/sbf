# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from src.sbfVersion import computeVersionNumber

class Use_boost( IUse ):
	def getName( self ):
		return 'boost'

	def getVersions( self ):
		if self.platform == 'win':
			return [ '1-54-0', '1-56-0', '1-53-0', '1-52-0', '1-51-0', '1-50-0', '1-49-0', '1-48-0', '1-47-0', '1-46-1' ]
		else:
			return [ '1-56-0', '1-54-0', '1-53-0', '1-52-0', '1-51-0', '1-50-0', '1-49-0', '1-48-0', '1-47-0', '1-46-1' ]


	def getCPPDEFINES( self, version ):
		versionf = computeVersionNumber( version.split('-') ) * 1000000 # * 1000 * 1000
		if self.platform == 'win':
			if version in ['1-54-0', '1-56-0']:
				return [ 'BOOST_ALL_DYN_LINK', ('SBF_BOOST_VERSION', "{}".format(int(versionf))), 'BOOST_SIGNALS_NO_DEPRECATION_WARNING' ]
			else:
				return [ 'BOOST_ALL_DYN_LINK', ('SBF_BOOST_VERSION', "{}".format(int(versionf))) ]
		else:
			return [ ('SBF_BOOST_VERSION', "{}".format(int(versionf))), 'BOOST_SIGNALS_NO_DEPRECATION_WARNING' ]


	def getLIBS( self, version ):
		if self.platform == 'win':

			# vc version
			vcVersionDict = {	12 : 'vc120',
								11 : 'vc110',
								10 : 'vc100',
								9  : 'vc90',
								8  : 'vc80'	}

			vc = vcVersionDict.get(self.ccVersionNumber, None)
			if not vc:
				return

			# configuration
			if self.config == 'release':
				conf = 'mt'
			else:
				conf = 'mt-gd'

			# boost shared libraries
			genPakLibs = [	'boost_date_time-{vc}-{conf}-{ver}', 'boost_filesystem-{vc}-{conf}-{ver}', 'boost_graph-{vc}-{conf}-{ver}',
							'boost_iostreams-{vc}-{conf}-{ver}', 'boost_math_c99-{vc}-{conf}-{ver}', 'boost_math_c99f-{vc}-{conf}-{ver}',
							'boost_math_c99l-{vc}-{conf}-{ver}', 'boost_math_tr1-{vc}-{conf}-{ver}', 'boost_math_tr1f-{vc}-{conf}-{ver}',
							'boost_math_tr1l-{vc}-{conf}-{ver}', 'boost_prg_exec_monitor-{vc}-{conf}-{ver}', 'boost_program_options-{vc}-{conf}-{ver}',
							'boost_python-{vc}-{conf}-{ver}', 'boost_random-{vc}-{conf}-{ver}', 'boost_regex-{vc}-{conf}-{ver}',
							'boost_serialization-{vc}-{conf}-{ver}', 'boost_signals-{vc}-{conf}-{ver}', 'boost_system-{vc}-{conf}-{ver}',
							'boost_thread-{vc}-{conf}-{ver}', 'boost_unit_test_framework-{vc}-{conf}-{ver}', 'boost_wave-{vc}-{conf}-{ver}',
							'boost_wserialization-{vc}-{conf}-{ver}' ]
			genPakLibs2 = [	'boost_chrono-{vc}-{conf}-{ver}' ]
			genPakLibs3 = [	'boost_locale-{vc}-{conf}-{ver}', 'boost_timer-{vc}-{conf}-{ver}' ]
			genPakLibs4 = [	'boost_context-{vc}-{conf}-{ver}' ]
			genPakLibs5 = [	'boost_atomic-{vc}-{conf}-{ver}' ]
			#genPakLibs6 = [ 'boost_log_setup-{vc}-{conf}-{ver}', 'boost_log-{vc}-{conf}-{ver}' ]

			ver = version[0:4].replace('-', '_') # 1-56-0 => 1_56

			if version in ['1-54-0', '1-56-0']:
				# autolinking and dev package, so nothing to do.
				return [], []
			elif version in ['1-53-0']:
				# autolinking, so nothing to do.
				pakLibs = [ lib.format( vc=vc, conf=conf, ver=ver ) for lib in genPakLibs + genPakLibs2 + genPakLibs3 + genPakLibs4 + genPakLibs5 ]
				return [], pakLibs
			elif version in ['1-52-0', '1-51-0']:
				# autolinking, so nothing to do.
				pakLibs = [ lib.format( vc=vc, conf=conf, ver=ver ) for lib in genPakLibs + genPakLibs2 + genPakLibs3 + genPakLibs4 ]
				return [], pakLibs
			elif version in ['1-50-0', '1-49-0', '1-48-0']:
				# autolinking, so nothing to do.
				pakLibs = [ lib.format( vc=vc, conf=conf, ver=ver ) for lib in genPakLibs + genPakLibs2 + genPakLibs3 ]
				return [], pakLibs
			elif version == '1-47-0':
				# autolinking, so nothing to do.
				pakLibs = [ lib.format( vc=vc, conf=conf, ver=ver ) for lib in genPakLibs + genPakLibs2 ]
				return [], pakLibs
			elif version == '1-46-1':
				# autolinking, so nothing to do.
				ver = '1_46_1'
				pakLibs = [ lib.format( vc=vc, conf=conf, ver=ver ) for lib in genPakLibs ]
				return [], pakLibs
		elif self.platform == 'posix' and version in ['1-56-0']:
			libs = [	'libboost_atomic.so', 'libboost_bzip2.so', 'libboost_chrono.so', 'libboost_container.so', 'libboost_context.so', 'libboost_coroutine.so',
					'libboost_date_time.so', 'libboost_filesystem.so', 'libboost_graph.so', 'libboost_iostreams.so', 'libboost_locale.so', 'libboost_log.so',
					'libboost_log_setup.so', 'libboost_math_c99.so', 'libboost_math_c99f.so', 'libboost_math_c99l.so', 'libboost_math_tr1.so', 'libboost_math_tr1f.so',
					'libboost_math_tr1l.so', 'libboost_prg_exec_monitor.so', 'libboost_program_options.so', 'libboost_python.so', 'libboost_random.so',
					'libboost_regex.so', 'libboost_serialization.so', 'libboost_signals.so', 'libboost_system.so', 'libboost_thread.so', 'libboost_timer.so',
					'libboost_unit_test_framework.so', 'libboost_wave.so', 'libboost_wserialization.so', 'libboost_zlib.so']

			return libs, libs

	def hasRuntimePackage( self, version ):
		return version in ['1-56-0', '1-54-0']
