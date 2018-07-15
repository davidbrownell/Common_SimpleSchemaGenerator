# ----------------------------------------------------------------------
# |  
# |  Metadata.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-12 10:24:18
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the Metadata object and default metadata"""

import os
import sys

from collections import OrderedDict, namedtuple

import CommonEnvironment
from CommonEnvironment.TypeInfo.FundamentalTypes.All import *

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class Metadata(object):
    """Metadata that can be applied to SimpleSchema items"""

    class DoesNotExist(object): pass

    # ----------------------------------------------------------------------
    def __init__( self,
                  name,
                  type_info,
                  default_value=DoesNotExist,           # Can be specific value or def Func(item) -> value
                ):
        self.Name                           = name
        self.TypeInfo                       = type_info

        if default_value == DoesNotExist:
            default_value_func = None
        elif callable(default_value):
            default_value_func = default_value
        else:
            default_value_func = lambda item: default_value

        self.DefaultValueFunc               = default_value_func

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)

# ----------------------------------------------------------------------
class MetadataInfo(object):
    # ----------------------------------------------------------------------
    def __init__( self,
                  required_metadata_items=None,
                  optional_metadata_items=None,
                ):
        self.RequiredMetadataItems          = required_metadata_items or []
        self.OptionalMetadataItems          = optional_metadata_items or []

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)

# ----------------------------------------------------------------------
class FundamentalMetadataInfo(MetadataInfo):
    # ----------------------------------------------------------------------
    def __init__( self, 
                  type_info_class,
                  required_metadata_items=None,
                  optional_metadata_items=None,
                ):
        super(FundamentalMetadataInfo, self).__init__(required_metadata_items, optional_metadata_items)
        self.TypeInfoClass                  = type_info_class
        
    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)

# ----------------------------------------------------------------------
# |  
# |  Public Data
# |  
# ----------------------------------------------------------------------
NAME_OVERRIDE_METADATA_NAME                 = "name"
PLURAL_METADATA_NAME                        = "plural"

UNIVERSAL_METADATA_INFO                     = MetadataInfo( optional_metadata_items=[ # Override the name of the object. This is useful when the element should have a name that would otherwise
                                                                                      # be reserved by the system (date, string, filename, etc.)
                                                                                      #
                                                                                      # Note that this metadata value is processed during Parsing and not made available within an Element.
                                                                                      Metadata(NAME_OVERRIDE_METADATA_NAME, StringTypeInfo()),
                                                                                      
                                                                                      Metadata("description", StringTypeInfo(), default_value=''),
                                                                                    ],
                                                          )

COMPOUND_METADATA_INFO                      = MetadataInfo( optional_metadata_items=[ # By default, compound objects referencing other compound objects will aggregate the compound element's 
                                                                                      # data. Set this value to True if polymorphic behavior is desired instead.
                                                                                      Metadata("polymorphic", BoolTypeInfo()),

                                                                                      # Compound elements that reference polymorphic elements will be polymorphic as well unless this value
                                                                                      # is provided and set to True
                                                                                      Metadata("suppress_polymorphic", BoolTypeInfo()),
                                                                                    ],
                                                          )

SIMPLE_METADATA_INFO                        = MetadataInfo( optional_metadata_items=[ # Create a named child with this name for plugins that don't support simple objects
                                                                                      Metadata("fundamental_name", StringTypeInfo()),
                                                                                    ],
                                                          )

ANY_METADATA_INFO                           = MetadataInfo()

CUSTOM_METADATA_INFO                        = MetadataInfo( required_metadata_items=[ Metadata("type", StringTypeInfo()),
                                                                                    ],
                                                          )

VARIANT_METADATA_INFO                       = MetadataInfo()
REFERENCE_METADATA_INFO                     = MetadataInfo()
LIST_METADATA_INFO                          = MetadataInfo()
EXTENSION_METADATA_INFO                     = MetadataInfo()

COLLECTION_METADATA_INFO                    = MetadataInfo( optional_metadata_items=[ # Override automatic calculation of a plural name with this value
                                                                                      #
                                                                                      # Note that this metadata value is processed during Parsing and not made available within an Element.
                                                                                      Metadata(PLURAL_METADATA_NAME, StringTypeInfo()),

                                                                                      # Name of child element whose value should be unique across all children
                                                                                      Metadata("unique_key", StringTypeInfo()),

                                                                                      # Normally, a reference that is also a collection will break reference traversal and create a new dimension
                                                                                      # in a N-dimension array. However, sometimes we just want to refine the arity of a referenced collection.
                                                                                      Metadata("refines_arity", BoolTypeInfo()),
                                                                                    ],
                                                          )

OPTIONAL_METADATA_INFO                      = MetadataInfo( optional_metadata_items=[ Metadata("default", StringTypeInfo()),
                                                                                    ],
                                                          )


FUNDAMENTAL_TYPE_INFO_MAP                   = OrderedDict([ ( "bool", FundamentalMetadataInfo(BoolTypeInfo) ),
                                                            ( "datetime", FundamentalMetadataInfo(DateTimeTypeInfo) ),
                                                            ( "date", FundamentalMetadataInfo(DateTypeInfo) ),
                                                            ( "directory", FundamentalMetadataInfo( DirectoryTypeInfo,
                                                                                                    optional_metadata_items=[ Metadata("ensure_exists", BoolTypeInfo(), default_value=True),
                                                                                                                              Metadata("validation_expression", StringTypeInfo()),
                                                                                                                            ],
                                                                                                  ) ),
                                                            ( "duration", FundamentalMetadataInfo(DurationTypeInfo) ),
                                                            ( "enum", FundamentalMetadataInfo( EnumTypeInfo,
                                                                                               required_metadata_items=[ Metadata("values", StringTypeInfo(arity='+')),
                                                                                                                       ],
                                                                                               optional_metadata_items=[ Metadata("friendly_values", StringTypeInfo(arity='+')),
                                                                                                                       ],
                                                                                             ) ),
                                                            ( "filename", FundamentalMetadataInfo( FilenameTypeInfo,
                                                                                                   optional_metadata_items=[ Metadata("ensure_exists", BoolTypeInfo(), default_value=True),
                                                                                                                             Metadata("validation_expression", StringTypeInfo()),
                                                                                                                             Metadata("match_any", BoolTypeInfo(), default_value=False),
                                                                                                                           ],
                                                                                                 ) ),
                                                            ( "number", FundamentalMetadataInfo( FloatTypeInfo,
                                                                                                 optional_metadata_items=[ Metadata("min", FloatTypeInfo()),
                                                                                                                           Metadata("max", FloatTypeInfo()),
                                                                                                                         ],
                                                                                               ) ),
                                                            ( "guid", FundamentalMetadataInfo(GuidTypeInfo) ),
                                                            ( "int", FundamentalMetadataInfo( IntTypeInfo,
                                                                                              optional_metadata_items=[ Metadata("min", IntTypeInfo()),
                                                                                                                        Metadata("max", IntTypeInfo()),
                                                                                                                        Metadata("bytes", EnumTypeInfo([ 1, 2, 4, 8, ])),
                                                                                                                        Metadata("unsigned", BoolTypeInfo(), default_value=False),
                                                                                                                      ],
                                                                                            ) ),
                                                            ( "string", FundamentalMetadataInfo( StringTypeInfo,
                                                                                                 optional_metadata_items=[ Metadata("min_length", IntTypeInfo(min=0)),
                                                                                                                           Metadata("max_length", IntTypeInfo(min=0)),
                                                                                                                           Metadata("validation_expression", StringTypeInfo()),
                                                                                                                         ],
                                                                                               ) ),
                                                            ( "time", FundamentalMetadataInfo(TimeTypeInfo) ),
                                                            ( "uri", FundamentalMetadataInfo(UriTypeInfo) ),
                                                          ])