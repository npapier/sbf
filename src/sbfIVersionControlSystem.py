# SConsBuildFramework - Copyright (C) 2009, 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class IVersionControlSystem :
	"""Interface to version control system"""

	def __init__( self ):
		pass

	def add( self, myProjectPathName, myProject ):
		raise AssertionError("'add' operation is not available in the version control system.")

	def checkout( self, myProjectPathName, myProject ):
		raise AssertionError("'checkout' operation is not available in the version control system.")

	def export( self ):
		raise AssertionError("'export' operation is not available in the version control system.")

	def clean( self, myProjectPathName, myProject ):
		raise AssertionError("'clean' operation is not available in the version control system.")

	def status( self, myProjectPathName, myProject ):
		raise AssertionError("'status' operation is not available in the version control system.")

	def update( self, myProjectPathName, myProject ):
		raise AssertionError("'update' operation is not available in the version control system.")

	def getUrl( self, path ):
		raise AssertionError("'getUrl' method is not available in the version control system.")	
