# ----------------------------------------------------------------------
# |
# |  SimpleSchemaVisitor.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2020-09-15 22:01:12
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2020-22
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the SimpleSchemaVisitor object"""

import os

from collections import OrderedDict
from enum import Enum, auto

import six

import CommonEnvironment
from CommonEnvironment import Interface
from CommonEnvironment.TypeInfo.FundamentalTypes.Visitor import Visitor as VisitorBase

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# <Parameters differ from overridden...> pylint: disable = W0221

# ----------------------------------------------------------------------
class SimpleSchemaType(Enum):
    Standard                                = auto()
    Attribute                               = auto()
    Definition                              = auto()


# ----------------------------------------------------------------------
@Interface.staticderived
class SimpleSchemaVisitor(VisitorBase):
    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnBool(
        cls,
        type_info,
        name,
        simple_schema_type=SimpleSchemaType.Standard,
    ):
        return cls._Impl("bool", name, {}, type_info.Arity, simple_schema_type)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnDateTime(
        cls,
        type_info,
        name,
        simple_schema_type=SimpleSchemaType.Standard,
    ):
        return cls._Impl("datetime", name, {}, type_info.Arity, simple_schema_type)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnDate(
        cls,
        type_info,
        name,
        simple_schema_type=SimpleSchemaType.Standard,
    ):
        return cls._Impl("date", name, {}, type_info.Arity, simple_schema_type)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnDirectory(
        cls,
        type_info,
        name,
        simple_schema_type=SimpleSchemaType.Standard,
    ):
        args = OrderedDict()

        if not type_info.EnsureExists:
            args["ensure_exists"] = False
        if type_info.ValidationExpression is not None:
            args["validation_expression"] = '"{}"'.format(type_info.ValidationExpression)

        return cls._Impl("directory", name, args, type_info.Arity, simple_schema_type)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnDuration(
        cls,
        type_info,
        name,
        simple_schema_type=SimpleSchemaType.Standard,
    ):
        return cls._Impl("duration", name, {}, type_info.Arity, simple_schema_type)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnEnum(
        cls,
        type_info,
        name,
        simple_schema_type=SimpleSchemaType.Standard,
    ):
        args = OrderedDict()

        # ----------------------------------------------------------------------
        def ToListString(values):
            return "[{}]".format(", ".join(['"{}"'.format(value) for value in values]))

        # ----------------------------------------------------------------------

        args["values"] = ToListString(type_info.Values)

        if type_info.FriendlyValues:
            args["friendly_values"] = ToListString(type_info.FriendlyValues)

        return cls._Impl("enum", name, args, type_info.Arity, simple_schema_type)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnFilename(
        cls,
        type_info,
        name,
        simple_schema_type=SimpleSchemaType.Standard,
    ):
        args = OrderedDict()

        if not type_info.EnsureExists:
            args["ensure_exists"] = False
        if type_info.MatchAny:
            args["match_any"] = True
        if type_info.ValidationExpression:
            args["validation_expression"] = '"{}"'.format(type_info.ValidationExpression)

        return cls._Impl("filename", name, args, type_info.Arity, simple_schema_type)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnFloat(
        cls,
        type_info,
        name,
        simple_schema_type=SimpleSchemaType.Standard,
    ):
        args = OrderedDict()

        if type_info.Min is not None:
            args["min"] = type_info.Min
        if type_info.Max is not None:
            args["max"] = type_info.Max

        return cls._Impl("number", name, args, type_info.Arity, simple_schema_type)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnGuid(
        cls,
        type_info,
        name,
        simple_schema_type=SimpleSchemaType.Standard,
    ):
        return cls._Impl("guid", name, {}, type_info.Arity, simple_schema_type)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnInt(
        cls,
        type_info,
        name,
        simple_schema_type=SimpleSchemaType.Standard,
    ):
        args = OrderedDict()

        if type_info.Min is not None:
            args["min"] = type_info.Min
        if type_info.Max is not None:
            args["max"] = type_info.Max
        if type_info.Bytes is not None:
            args["bytes"] = type_info.Bytes
        if type_info.Unsigned:
            args["unsigned"] = True

        return cls._Impl("int", name, args, type_info.Arity, simple_schema_type)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnString(
        cls,
        type_info,
        name,
        simple_schema_type=SimpleSchemaType.Standard,
    ):
        args = OrderedDict()

        if type_info.ValidationExpression is not None:
            args["validation_expression"] = '"{}"'.format(type_info.ValidationExpression)
        if type_info.MinLength is not None:
            args["min_length"] = type_info.MinLength
        if type_info.MaxLength is not None:
            args["max_length"] = type_info.MaxLength

        return cls._Impl("string", name, args, type_info.Arity, simple_schema_type)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnTime(
        cls,
        type_info,
        name,
        simple_schema_type=SimpleSchemaType.Standard,
    ):
        return cls._Impl("time", name, {}, type_info.Arity, simple_schema_type)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnUri(
        cls,
        type_info,
        name,
        simple_schema_type=SimpleSchemaType.Standard,
    ):
        return cls._Impl("uri", name, {}, type_info.Arity, simple_schema_type)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def _Impl(typ, name, args, arity, simple_schema_type):
        if simple_schema_type == SimpleSchemaType.Standard:
            delimiters = ["<", ">"]
        elif simple_schema_type == SimpleSchemaType.Attribute:
            delimiters = ["[", "]"]
        elif simple_schema_type == SimpleSchemaType.Definition:
            delimiters = ["(", ")"]
        else:
            assert False, simple_schema_type

        arity = arity.ToString()

        return "{open}{name}{type}{args}{arity}{close}".format(
            open=delimiters[0],
            name="{} ".format(name) if name else "",
            type=typ,
            args=" {}".format(" ".join(["{}={}".format(k, v) for k, v in six.iteritems(args)])) if args else "",
            arity=" {}".format(arity) if arity else "",
            close=delimiters[1],
        )
