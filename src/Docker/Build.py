# ----------------------------------------------------------------------
# |
# |  Build.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-17 13:07:58
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Builds the Common_SimpleSchemaGenerator Docker image"""

import os
import sys

import CommonEnvironment
from CommonEnvironment import BuildImpl
from CommonEnvironment.BuildImpl import DockerBuildImpl
from CommonEnvironment import CommandLine

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

APPLICATION_NAME                            = "Docker_Common_SimpleSchemaGenerator"

Build                                       = DockerBuildImpl.CreateRepositoryBuildFunc(
    "Common_SimpleSchemaGenerator",
    os.path.join(_script_dir, "..", ".."),
    "dbrownell",
    "common_simpleschemagenerator",
    "dbrownell/common_environmentex:base",
    "David Brownell <db@DavidBrownell.com>",
    repository_source_excludes=[],
    repository_activation_configurations=[],
)

Clean                                       = DockerBuildImpl.CreateRepositoryCleanFunc()

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(
            BuildImpl.Main(
                BuildImpl.Configuration(
                    name=APPLICATION_NAME,
                    requires_output_dir=False,
                ),
            ),
        )
    except KeyboardInterrupt:
        pass
