# SConsBuildFramework - Copyright (C) 2009, 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class IVersionControlSystem:
	"""Interface to version control system"""

	def __init__( self ):
		pass


	def add( self, myProjectPathName, myProject ):
		raise AssertionError("'add' operation is not available in the version control system.")


	def _checkout( self, url, path, revision ):
		"""Checkout the repository at url into the location specified by path to the given revision (could be None)."""
		raise AssertionError("'_checkout' operation is not available in the version control system.")
	def checkout( self, myProjectPathName, myProject ):
		raise AssertionError("'checkout' operation is not available in the version control system.")


	def _export( self, svnUrl, exportPath, projectName ):
		raise AssertionError("'_export' operation is not available in the version control system.")
	#def export( self, myProjectPathName, myProject ):
	#	raise AssertionError("'export' operation is not available in the version control system.")


	def clean( self, myProjectPathName, myProject ):
		raise AssertionError("'clean' operation is not available in the version control system.")


	def relocate( self, myProjectPathName, myProject ):
		raise AssertionError("'relocate' operation is not available in the version control system.")


	def _update( self, path, revision ):
		"""Updates the working copy at path to the specified revision (could be None)."""
		raise AssertionError("'_update' operation is not available in the version control system.")
	def update( self, myProjectPathName, myProject ):
		raise AssertionError("'update' operation is not available in the version control system.")


	def copy( self, sourcePath, destination, message ):
		raise AssertionError("'copy' operation is not available in the version control system.")


	def remove( self, pathToWC, branchToRemove, message ):
		raise AssertionError("'remove' operation is not available in the version control system.")


	def status( self, myProjectPathName, myProject ):
		raise AssertionError("'status' operation is not available in the version control system.")


	def _listDir( self, urlOrPath, recurse = False, revisionNumber = None ):
		raise AssertionError("'_listDir' method is not available in the version control system.")

	def listBranch( self, projectPathName, branch ):
		raise AssertionError("'listBranch' method is not available in the version control system.")


	def getAllVersionedFiles( self, myProjectPathName ):
		raise AssertionError("'getAllVersionedFiles' method is not available in the version control system.")


	def getUrl( self, path ):
		raise AssertionError("'getUrl' method is not available in the version control system.")

	def getSplitUrl( self, urlOrPath ):
		raise AssertionError("'getSplitUrl' method is not available in the version control system.")

	def getRevision( self, urlOrPath ):
		raise AssertionError("'getRevision' method is not available in the version control system.")
