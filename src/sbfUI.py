# SConsBuildFramework - Copyright (C) 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

def askQuestion( question, choicesList, queryUser = True ):
	"""The given question is written to standard output followed by a textual description of the available choices.
	The first choise in choicesList would be the default choice. The answer is returned as a string.
	If queryUser parameter is False, then question is not asked and the default choice is returned"""

	choicesText = ''
	selectors = []
	for choice in choicesList:
		selector = choice[0]
		selectors.append( selector )

		choiceText = '({0}){1}'.format( selector, choice[1:] )
		if len(choicesText) == 0:
			choicesText = choiceText.upper()
		else:
			choicesText += ', ' + choiceText

	defaultSelector = selectors[0]

	# Don't ask question
	if not queryUser:
		return defaultSelector.lower()

	# Asks question
	while( True ):
		answer = raw_input('{0} ? {1} '.format( question, choicesText ))

		if len(answer)==0:
			answer = defaultSelector

		if answer in selectors:
			break

	return answer.lower()


def ask( question, defaultValue, queryUser = True ):
	"""The given question is written to standard output followed by the default value (must be defined).
	The answer is returned as a string.
	If queryUser parameter is False, then question is not asked and the default choice is returned."""

	# Checks precondition
	if len(defaultValue)==0:
		raise AssertionError('Empty default value is not allowed.')

	# Don't ask question
	if not queryUser:
		return defaultValue.lower()

	# Asks question
	while( True ):
		answer = raw_input( '{0} (default={1}) ? '.format(question, defaultValue) )

		if len(answer)==0:
			answer = defaultValue

		if len(answer)!=0:
			break

	return answer.lower()
