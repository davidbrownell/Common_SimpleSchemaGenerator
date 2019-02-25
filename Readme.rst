===================
Common_SimpleSchema
===================

SimpleSchemaGenerator is a schema definition language and compiler able to process schema inputs and generate output based on a plugin architecture; plugins include:

  * JSON Schemas
  * XSD Schema
  * Python Serialization according to:
      * JSON
      * XML
      * YAML

Plugins can be created to extend this functionality. Example of possible uses are the generation of:

  * SqlAlchemy ORM objects
  * Swagger definitions
  * REST APIs
  * etc.

Contents
========
#. `Quick Start`_
#. License_
#. `Supported Platforms`_
#. Functionality_
#. `Docker Images`_
#. Dependencies_
#. Support_

Quick Start
===========
Setup_ and Activate_ are required to begin using this repository. Before running these scripts, please make sure that all Dependencies have been cloned.

.. _Setup:

Setup
  Setup installs/unpacks tools used during development activities and locates its repository dependencies (if any). Setup must be run on your machine after cloning the repository or after changing the file location of repositories that it depends upon (if any).

  ====================================  =====================================================
  Linux                                 ``Setup.sh``
  Windows                               ``Setup.cmd``
  Windows (PowerShell)                  ``Setup.ps1``
  ====================================  =====================================================
  
.. _Activate:

Activate
  Activate prepares the current environment for development activities and must be run at least once in each terminal window.
  
  ====================================  =====================================================
  Linux                                 ``Activate.sh``
  Windows                               ``Activate.cmd``
  Windows (PowerShell)                  ``Activate.ps1``
  ====================================  =====================================================
  
License
=======
This repository is licensed under the `Boost Software License <https://www.boost.org/LICENSE_1_0.txt>`_. 

`GitHub <https://github.com>`_ describes this license as:

  A simple permissive license only requiring preservation of copyright and license notices for source (and not binary) distribution. Licensed works, modifications, and larger works may be distributed under different terms and without source code.

Supported Platforms
===================
========================  ======================  =========================================
Platform                  Scripting Environment   Version
========================  ======================  =========================================
Windows                   Cmd.exe                 Windows 10:

                                                  - October 2018 Update
                                                  - April 2018 Update

Windows                   PowerShell              Windows 10:

                                                  - October 2018 Update
                                                  - April 2018 Update

Linux                     Bash                    Ubuntu:

                                                  - 18.04
                                                  - 16.04
========================  ======================  =========================================

Functionality
=============
TODO: The SimpleSchema language is fully implemented, but not well documented. For now, examples are available at:

  * `AllTypes.SimpleSchema <src/SimpleSchemaGenerator/Plugins/Impl/AllTypes.SimpleSchema>`_
  * `FileSystemTest.SimpleSchema <src/SimpleSchemaGenerator/Plugins/Impl/FileSystemTest.SimpleSchema>`_
  * `Test.SimpleSchema <src/SimpleSchemaGenerator/Plugins/Impl/Test.SimpleSchema>`_

To invoke the SimpleSchemaGenerator, from an activated environment run:

  =========================  =======================================
  Linux                      ``SimpleSchemaGenerator.sh``
  Windows                    ``SimpleSchemaGenerator.cmd``
  Windows (PowerShell)       ``SimpleSchemaGenerator.ps1``
  =========================  =======================================

To generate a JSON Schema file on Windows:

  ``SimpleSchemaGenerator.cmd Generate JsonSchema MyFile <output directory> /input=<input_filename>``

Docker Images
=============
Docker images of Common_SimpleSchemaGenerator are generated periodically.

================================================  ==========================================
dbrownell/common_simpleschemagenerator:standard   An environment suitable for invoking SimpleSchemaGenerator.
dbrownell/common_simpleschemagenerator:base       An environment that is setup_ but not activated_ (useful as a base image for other Common_Environment-based images).
================================================  ==========================================

Dependencies
============
This repository is dependent upon these repositories.

======================================================================================  =================================
Repo Name                       Description
======================================================================================  =================================
`Common_EnvironmentEx <https://github.com/davidbrownell/Common_EnvironmentEx>`_         Enhances `Common_Environment` with libraries, scripts, and tools common to different development activities.
`Common_Environment_v3 <https://github.com/davidbrownell/Common_Environment_v3>`_       Foundational repository that implements functionality common to all development environments.
======================================================================================  =================================

Support
=======
For question or issues, please visit https://github.com/davidbrownell/Common_SimpleSchemaGenerator.
