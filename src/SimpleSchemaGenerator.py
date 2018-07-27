# ----------------------------------------------------------------------
# |  
# |  SimpleSchemaGenerator.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-06 07:42:45
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Process a SimpleSchema file using the specified generator."""

import os
import re
import sys
import textwrap

import six
from six.moves import cPickle as pickle

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment.StreamDecorator import StreamDecorator

from CommonEnvironmentEx.CompilerImpl.GeneratorPluginFrameworkImpl import GeneratorFactory
from CommonEnvironmentEx.Package import ApplyRelativePackage

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with ApplyRelativePackage():
    from .Plugin import Plugin as PluginBase
    from .Schema.Parse import ParseFiles

# ----------------------------------------------------------------------
PLUGINS                                     = GeneratorFactory.CreatePluginMap( "DEVELOPMENT_ENVIRONMENT_SIMPLE_SCHEMA_PLUGINS",
                                                                                os.path.join(_script_dir, "Plugins"),
                                                                                sys.stdout,
                                                                              )

_PluginTypeInfo                             = CommandLine.EnumTypeInfo(list(six.iterkeys(PLUGINS)))

# ----------------------------------------------------------------------
def _GetOptionalMetadata(*args, **kwargs):              return __GetOptionalMetadata(*args, **kwargs)
def _CreateContext(*args, **kwargs):                    return __CreateContext(*args, **kwargs)
def _Invoke(*args, **kwargs):                           return __Invoke(*args, **kwargs)

CodeGenerator                               = GeneratorFactory.CodeGeneratorFactory( PLUGINS,
                                                                                     "SimpleSchemaGenerator",
                                                                                     __doc__.replace('\n', ' '),
                                                                                     r".+\.SimpleSchema",
                                                                                     _GetOptionalMetadata,
                                                                                     _CreateContext,
                                                                                     _Invoke,
                                                                                   )

# ----------------------------------------------------------------------
@CommandLine.EntryPoint # BugBug
@CommandLine.Constraints( plugin=_PluginTypeInfo,
                          output_name=CommandLine.StringTypeInfo(),
                          output_dir=CommandLine.DirectoryTypeInfo(ensure_exists=False),
                          input=CommandLine.FilenameTypeInfo(match_any=True, arity='+'),
                          include=CommandLine.StringTypeInfo(arity='*'),
                          exclude=CommandLine.StringTypeInfo(arity='*'),
                          output_data_filename_prefix=CommandLine.StringTypeInfo(arity='?'),
                          plugin_arg=CommandLine.DictTypeInfo(require_exact_match=False, arity='?'),
                          output_stream=None,
                        )
def Generate( plugin,
              output_name,
              output_dir,
              input,
              include=None,
              exclude=None,
              output_data_filename_prefix=None,
              filter_unsupported_extensions=False,
              filter_unsupported_attributes=False,
              plugin_arg=None,
              force=False,
              output_stream=sys.stdout,
              verbose=False,
            ):
    """BugBug"""

    return GeneratorFactory.CommandLineGenerate( CodeGenerator,
                                                 input,
                                                 output_stream,
                                                 verbose,

                                                 plugin_name=plugin,
                                                 output_name=output_name,
                                                 output_dir=output_dir,

                                                 plugin_metadata=plugin_arg,

                                                 force=force,

                                                 includes=include,
                                                 excludes=exclude,
                                                 filter_unsupported_extensions=filter_unsupported_extensions,
                                                 filter_unsupported_attributes=filter_unsupported_attributes,
                                                 output_data_filename_prefix=output_data_filename_prefix,
                                               )

# ----------------------------------------------------------------------
@CommandLine.EntryPoint # BugBug
@CommandLine.Constraints( output_stream=None,
                        )
def Clean( output_stream=sys.stdout,
         ):
    """BugBug"""
    pass # BugBug

# ----------------------------------------------------------------------
def CommandLineSuffix():
    return textwrap.dedent(
        """\
        Where <plugin> can be one of the following:

        {}

        """).format('\n'.join([ "    - {0:<30}  {1}".format( "{}:".format(pi.Plugin.Name),
                                                             pi.Plugin.Description,
                                                           )
                                for pi in six.itervalues(PLUGINS)
                              ]))

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def __GetOptionalMetadata():
    return [ ( "includes", [] ),
             ( "excludes", [] ),
             ( "filter_unsupported_extensions", False ),
             ( "filter_unsupported_attributes", False ),
             ( "output_data_filename_prefix", None ),
           ]

# ----------------------------------------------------------------------
def __CreateContext(context, plugin):
    elements = ParseFiles( context["inputs"],
                           plugin,
                           context["filter_unsupported_extensions"],
                           context["filter_unsupported_attributes"],
                         )

    # Calculate the include indexes
    includes = [ re.compile("^{}$".format(include)) for include in context["includes"] ]
    excludes = [ re.compile("^{}$".format(exclude)) for exclude in context["excludes"] ]

    del context["includes"]
    del context["excludes"]

    include_indexes = range(len(elements))

    if excludes:
        include_indexes = [ index for index in include_indexes if not any(exclude for exclude in excludes if exclude.match(elements[index].Name)) ]

    if includes:
        include_indexes = [ index for index in include_indexes if any(include for include in includes if include.match(elements[index].Name)) ]

    # This is a bit strange, but to detect changes, we need to compare the data in the elements rather
    # than the elements themselves (as the elements will be different object instances during each invocation).
    # Therefore, save the data (via pickling) and remove the elements. During the invocation below, we will
    # deserialize the elements from the pickled data before invoking the plugin's Generate method.

    context["pickled_elements"] = pickle.dumps(elements)
    context["include_indexes"] = include_indexes

    return context

# ----------------------------------------------------------------------
def __Invoke( code_generator,
              invoke_reason,
              context,
              status_stream,
              verbose_stream,
              verbose,
              plugin,
            ):
    elements = pickle.loads(context["pickled_elements"])

    return plugin.Generate( code_generator,
                            invoke_reason,
                            context["inputs"],
                            context["output_filenames"],
                            context["output_name"],
                            elements,
                            context["include_indexes"],
                            status_stream,
                            verbose_stream,
                            verbose,
                            **context["plugin_settings"],
                          )
    
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass