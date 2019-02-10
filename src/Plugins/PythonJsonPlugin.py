# ----------------------------------------------------------------------
# |
# |  PythonJsonPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-09 13:19:16
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
from CommonEnvironment import StringHelpers

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
    Name                                                                                        = Interface.DerivedProperty("PythonJson")
    Description                                                                                 = Interface.DerivedProperty(
        "Creates python code that is able to serialize and deserialize python objects to JSON",
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
        # |  Public Properties
        ObjectTypeDesc                      = Interface.DerivedProperty("a JSON object")

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
                            {var_name} = json.load(f)
                    else:
                        {var_name} = json.loads({var_name})

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
        # |  Public Properties
        ObjectTypeDesc                      = Interface.DerivedProperty("a JSON object")

        # ----------------------------------------------------------------------
        # |  Methods
        @staticmethod
        @Interface.override
        def SerializeToString(var_name):
            return "_JsonToString({var_name}, pretty_print)".format(
                var_name=var_name,
            )

        # ----------------------------------------------------------------------
        @staticmethod
        @Interface.override
        def GetGlobalUtilityMethods(source_writer):
            return textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                def _JsonToString(obj, pretty_print):
                    if pretty_print:
                        return json.dumps(obj, cls=JsonEncoder, indent=2, separators=[", ", " : "])
                    else:
                        return json.dumps(obj, cls=JsonEncoder)
                """,
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
                import json

                from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.JsonSerialization import JsonSerialization

                # ----------------------------------------------------------------------
                class JsonEncoder(json.JSONEncoder):
                    def default(self, o):
                        return o.__dict__


                """,
            ),
        )

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def _WriteFileFooter(output_stream):
        # Nothing to do here
        pass
