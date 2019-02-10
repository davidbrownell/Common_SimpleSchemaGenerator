# ----------------------------------------------------------------------
# |
# |  PythonYamlPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-10 08:36:02
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the Plugin object"""

import os
import textwrap

import CommonEnvironment
from CommonEnvironment import Interface

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

with InitRelativeImports():
    from .Impl.PythonSerializationImpl import PythonSerializationImpl

    from .Impl.StatementWriters.PythonDestinationStatementWriter import PythonDestinationStatementWriter
    from .Impl.StatementWriters.PythonSourceStatementWriter import PythonSourceStatementWriter

# ----------------------------------------------------------------------
@Interface.staticderived
@Interface.clsinit
class Plugin(PythonSerializationImpl):
    # ----------------------------------------------------------------------
    # |  Properties
    Name                                                                                        = Interface.DerivedProperty("PythonYaml")
    Description                                                                                 = Interface.DerivedProperty(
        "Creates python code that is able to serialize and deserialize python objects to YAML",
    )

    # ----------------------------------------------------------------------
    # |  Methods
    @classmethod
    @Interface.override
    def GetAdditionalGeneratorItems(cls, context):
        return [_script_fullpath, PythonDestinationStatementWriter, PythonSourceStatementWriter] + super(
            Plugin,
            cls,
        ).GetAdditionalGeneratorItems(context)

    # ----------------------------------------------------------------------
    # |  Private Types
    @Interface.staticderived
    class SourceStatementWriter(PythonSourceStatementWriter):
        # ----------------------------------------------------------------------
        # |  Properties
        ObjectTypeDesc                      = Interface.DerivedProperty("a YAML object")

        # ----------------------------------------------------------------------
        # |  Methods
        @classmethod
        @Interface.override
        def ConvenienceConversions(cls, var_name, element):
            return textwrap.dedent(
                """\
                if isinstance({var_name}, six.string_types):
                    if os.path.isfile({var_name}):
                        with open({var_name}) as f:
                            {var_name} = rtyaml.load(f)
                    else:
                        {var_name} = rtyaml.load({var_name})

                {super}
                """,
            ).format(
                var_name=var_name,
                super=super(Plugin.SourceStatementWriter, cls).ConvenienceConversions(
                    var_name,
                    element,
                ),
            )

    # ----------------------------------------------------------------------
    @Interface.staticderived
    class DestinationStatementWriter(PythonDestinationStatementWriter):
        # ----------------------------------------------------------------------
        # |  Properties
        ObjectTypeDesc                      = Interface.DerivedProperty("a YAML object")

        # ----------------------------------------------------------------------
        # |  Methods
        @staticmethod
        @Interface.override
        def SerializeToString(var_name):
            return "rtyaml.dump({var_name})".format(
                var_name=var_name,
            )

    # ----------------------------------------------------------------------
    # |  Private Properties
    _SupportAttributes                      = Interface.DerivedProperty(False)
    _SupportAnyElements                     = Interface.DerivedProperty(True)
    _TypeInfoSerializationName              = Interface.DerivedProperty("JsonSerialization")

    _SourceStatementWriter                  = Interface.DerivedProperty(SourceStatementWriter)
    _DestinationStatementWriter             = Interface.DerivedProperty(DestinationStatementWriter)

    # ----------------------------------------------------------------------
    # |  Private Methods
    @staticmethod
    @Interface.override
    def _WriteFileHeader(output_stream):
        output_stream.write(
            textwrap.dedent(
                """\
                import rtyaml

                from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.JsonSerialization import JsonSerialization


                """,
            ),
        )

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def _WriteFileFooter(output_stream):
        # Nothing to do here
        pass
