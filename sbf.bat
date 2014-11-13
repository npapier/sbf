:: Find python from an explicit location relative to SConsBuildFramework
@setlocal
:: python path is hardcoded.
@IF EXIST "%~dp0runtime\WinPython\python\python.exe" (
	@SET SBF_PYTHON_HOME=%~dp0runtime\WinPython\python
	@SET SBF_PYTHON_SCRIPTS=%~dp0runtime\WinPython\python\Scripts
	@GOTO execScons
)

@scons.bat %*
@if not %ERRORLEVEL% == 0 goto noPython
@exit /B %ERRORLEVEL%

@:noPython
@echo Unable to locate python and/or scons.bat
@echo python is searched in SConsBuildFramework or in PATH
@exit /B %ERRORLEVEL%

:execScons
:: Ensure that the python embedded in SConsBuildFramework would be used
@SET PATH=%SBF_PYTHON_HOME%;%SBF_PYTHON_SCRIPTS%;%PATH%
@scons.bat %*
@exit /B %ERRORLEVEL%