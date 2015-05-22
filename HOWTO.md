# Introduction #

This document is an informal, often short, description of how to accomplish some specific task with SConsBuildFramework

## how to select MS Visual C++ toolchain version when multiple versions are installed ##

By default, SConsBuildFramework uses the highest installed version of MSVS for the compiler.

To change this, you must add in sbf main configuration file `clVersion = '2005Exp'` for Visual C++ 2005 Express
or if you prefer `clVersion = '8.0Exp'`


## how to tell sbf to ignore a file in the share directory of a project ##

All files starting with an underscore in 'share' directory of a project are ignored by sbf.


## When do I have to clean my projects using 'scons debug mrproper' and 'scons release mrproper' ? ##

Clean your projects, each time a package containing an external dependency is updated (by using **scons sbfpak**).

## What is the recommended way to update a project ? ##
Just run the following commands in the project directory (in this order):
  * 'scons svnupdate'
  * 'scons svncheckout'
  * 'scons pakupdate'

## What is the recommended way to build a project ? ##
Just run the following commands in the project directory:
  * to build the release version: 'scons release'. Release is the default configuration, so just run 'scons'.
  * to build the debug version: 'scons debug'
  * to build the project only (i.e. avoiding any build dependencies) : 'scons --nodeps' or 'scons --nd'.


## How to generate a project snapshot containing all source code, external libraries and compiler/tools that are needed to rebuild the project ? ##
  * 'sbfInit' (choose the project name and the desired branch or tag)
  * Restart your command prompt to take care of the new SConsBuildFramework (SCONS\_BUILD\_FRAMEWORK and PATH environment variables).
  * Extract SConsBuildFrameworkRedistributable.zip (found in _C:\Program Files (x86)\SConsBuildFramework\Redistributable_ directory) in $SCONS\_BUILD\_FRAMEWORK.
  * 'cd $SCONS\_BUILD\_FRAMEWORK; cd ../projectName'
  * 'scons svnCheckout'
  * 'scons pakUpdate'
  * 'cd ../..'
  * 'mkdir sbfPak'
  * 'cp localExt\_win32\_cl10-0Exp/sbfPakDB/`*`.zip sbfPak'. Copy all zip files from localExt\_win32\_cl10-0Exp/sbfPakDB into sbfPak.
  * 'rm -r build local localExt\_win32\_cl10-0Exp'. Remove build, local and localExt\_win32\_cl10-0Exp directories.
  * copy SConsBuildFramework\_X\_Y.exe and installSilentlySConsBuildFramework.bat into current directory (they are in \\ORANGE\files\Install\Apps\dev\SConsBuildFramework).

## How to use a project snapshot ? ##
  * To install the development environment (this is only needed to be done once for the computer) :
    * just launch 'SConsBuildFramework\_X\_Y.exe /S' to install (almost) silently all requested programs (Doxygen, graphviz, NSIS, pyreadline, pysvn, pywin32, SCons, Python, SConsBuildFramework).
    * Install Visual C++ 2010 using one of the following methods :
      1. Go to the 'Start Menu/SConsBuildFramework' and select 'Launch Visual C++ 2010 setup' the install Visual C++ 2010 (you can uncheck SilverLight and SQL server). This is the web download version that download program from the Microsoft site.
      1. Burn the disc image of Visual C++ and install it.
  * To compile the software
    * Launch the Windows Command Processor (i.e. cmd.exe), and change the current directory to bin/SConsBuildFramework.
    * Launch the 'sbfInit.py -s' script to configure the environment for this set of projects.
    * Launch a new Windows Command Processor (i.e. cmd.exe), and change the current directory to bin/myProject.
    * 'scons pakUpdate' to install the external dependencies.
    * 'scons' to build the project. The compilation result are placed in local/bin directory.
    * 'scons nsis' to generate the installation program. It could be found in the build/nsis/myProject\_version\_platform\_compiler\_setup\_date directory (the file myProject\_version\_date\_setup.exe). Portable version (i.e. the program able to run without being installed) is the whole directory found in 'build/nsis/myProject\_version\_platform\_compiler\_portable\_date' containing the project executable in 'bin' subdirectory.
    * 'scons zipportable' generate a zip file containing a portable version of the program in directory 'local/portable'.
    * 'scons dox' to generate the code documentation. It could be found in the 'local/doc/myProject/version/index.html'.

