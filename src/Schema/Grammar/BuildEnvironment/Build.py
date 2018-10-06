# ----------------------------------------------------------------------
# |  
# |  Build.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-03 07:48:22
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Builds the SimpleSchema grammar"""

import os
import sys

import CommonEnvironment
from CommonEnvironment import BuildImpl
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment.Shell.All import CurrentShell
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints( output_stream=None,
                        )
def Build( output_stream=sys.stdout,
         ):
    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     prefix="\nResults: ",
                                                     suffix='\n',
                                                   ) as dm:
        input_file = os.path.join(_script_dir, "..", "SimpleSchema.g4")
        assert os.path.isfile(input_file), input_file

        output_dir = os.path.join(_script_dir, "..", "GeneratedCode")

        command_line = '{script} Compile Python3 -o "{output_dir}" -no-listener -visitor "{input_file}"' \
                            .format( script=CurrentShell.CreateScriptName("ANTLR"),
                                     output_dir=output_dir,
                                     input_file=input_file,
                                   )

        dm.result = Process.Execute(command_line, dm.stream)
        return dm.result

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints( output_stream=None,
                        )
def Clean( output_stream=sys.stdout,
         ):
    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     prefix="\nResults: ",
                                                     suffix='\n',
                                                   ) as dm:
        FileSystem.RemoveTree(os.path.join(_script_dir, "..", "GeneratedCode"))
        return dm.result

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(BuildImpl.Main(BuildImpl.Configuration( name="SimpleSchemaGenerator_Grammar_Build",
                                                         requires_output_dir=False,
                                                         priority=1,
                                                       )))
    except KeyboardInterrupt:
        pass
