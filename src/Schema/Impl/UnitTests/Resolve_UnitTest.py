# ----------------------------------------------------------------------
# |  
# |  Resolve_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-26 20:07:28
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for Resolve.py"""

import os
import sys
import textwrap
import unittest

from collections import OrderedDict

import CommonEnvironment
from CommonEnvironment.TypeInfo.FundamentalTypes.All import *

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with InitRelativeImports():
    from ..Item import *
    from ..Resolve import *
    
    from ... import Exceptions
    
    from ....Plugin import ParseFlag

# ----------------------------------------------------------------------
class ConfigurationSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Flattening(self):
        plugin, item = self._CreatePluginAndItem()

        item.config[plugin.Name][0]["foo"] = MetadataValue(10, MetadataSource.Config, "<source>", 0, 0)
        item.config[plugin.Name].append({ "bar" : MetadataValue(20, MetadataSource.Config, "<source>", 0, 0) })
        item.config["DoesNotExist"] = [ { "baz" : MetadataValue(30, MetadataSource.Config, "<source>", 0, 0) }, ]

        root = Resolve(item, plugin)

        self.assertEqual(set(six.iterkeys(root.metadata.Values)), set([ "foo", "bar", "description", ]))
        self.assertEqual(root.metadata.Values["foo"].Value, 10)
        self.assertEqual(root.metadata.Values["bar"].Value, 20)

    # ----------------------------------------------------------------------
    def _CreatePluginAndItem(self):
        item = _CreateItem()
        item.config = OrderedDict()

        plugin = _CreatePlugin()

        item.config[plugin.Name] = [ {}, ]
        item.metadata = Metadata( {},
                                  item.Source,
                                  item.Line,
                                  item.Column,
                                )

        return plugin, item

# ----------------------------------------------------------------------
class FundamentalSuite(unittest.TestCase):
    # ----------------------------------------------------------------------
    def test_String(self):
        parent = _CreateItem()
        parent.config = {}

        child1 = _CreateItem( declaration_type=Item.DeclarationType.Declaration,
                              parent=parent,
                            )

        child1.name = "child1"
        child1.reference = "string"

        root = Resolve(parent, _CreatePlugin())

        self.assertEqual(len(root.items), 1)
        self.assertEqual(root.items[0].name, "child1")
        self.assertEqual(root.items[0].element_type, Elements.FundamentalElement)
        self.assertEqual(root.items[0].reference, Attributes.FUNDAMENTAL_ATTRIBUTE_INFO_MAP["string"])

    # ----------------------------------------------------------------------
    def test_Any(self):
        parent = _CreateItem()
        parent.config = {}

        child1 = _CreateItem( declaration_type=Item.DeclarationType.Declaration,
                              parent=parent,
                            )
                            
        child1.name = "child1"
        child1.reference = "any"

        root = Resolve(parent, _CreatePlugin())

        self.assertEqual(len(root.items), 1)
        self.assertEqual(root.items[0].name, "child1")
        self.assertEqual(root.items[0].element_type, Elements.AnyElement)
        self.assertEqual(root.items[0].reference, Attributes.ANY_ATTRIBUTE_INFO)

    # ----------------------------------------------------------------------
    def test_Custom(self):
        parent = _CreateItem()
        parent.config = {}

        child1 = _CreateItem( declaration_type=Item.DeclarationType.Declaration,
                              parent=parent,
                            )

        child1.name = "child1"
        child1.reference = "custom"

        root = Resolve(parent, _CreatePlugin())

        self.assertEqual(len(root.items), 1)
        self.assertEqual(root.items[0].name, "child1")
        self.assertEqual(root.items[0].element_type, Elements.CustomElement)
        self.assertEqual(root.items[0].reference, Attributes.CUSTOM_ATTRIBUTE_INFO)

    # ----------------------------------------------------------------------
    def test_Variant(self):
        parent = _CreateItem()
        parent.config = {}

        child1 = _CreateItem( declaration_type=Item.DeclarationType.Declaration,
                              parent=parent,
                            )

        child1.name = "child1"
        child1.reference = [ ( "int", Metadata({}, "<source>", 0, 0) ),
                             ( "bool", Metadata({}, "<source>", 1, 1) ),
                             ( "string", Metadata({}, "<source>", 2, 2) ),
                           ]

        root = Resolve(parent, _CreatePlugin())

        self.assertEqual(len(root.items), 1)
        self.assertEqual(root.items[0].name, "child1")
        self.assertEqual(root.items[0].element_type, Elements.VariantElement)
        self.assertEqual(len(root.items[0].reference), 3)
        self.assertEqual(root.items[0].reference[0].element_type, Elements.FundamentalElement)
        self.assertEqual(root.items[0].reference[0].reference.TypeInfoClass, IntTypeInfo)
        self.assertEqual(root.items[0].reference[1].reference.TypeInfoClass, BoolTypeInfo)
        self.assertEqual(root.items[0].reference[2].reference.TypeInfoClass, StringTypeInfo)

# ----------------------------------------------------------------------
class ReferenceSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Fundamental(self):
        parent = _CreateItem()
        parent.config = {}

        child1 = _CreateItem( declaration_type=Item.DeclarationType.Declaration,
                              parent=parent,
                            )
        child1.name = "child1"
        child1.reference = "string"

        child2 = _CreateItem( declaration_type=Item.DeclarationType.Declaration,
                              parent=parent,
                            )
        child2.name = "child2"
        child2.reference = "child1"

        root = Resolve(parent, _CreatePlugin())

        self.assertEqual(len(root.items), 2)
        self.assertEqual(root.items[0].name, "child1")
        self.assertEqual(root.items[1].name, "child2")
        self.assertEqual(root.items[1].reference, root.items[0])
        self.assertEqual(root.items[1].element_type, Elements.ReferenceElement)

    # ----------------------------------------------------------------------
    def test_Object(self):
        parent = _CreateItem()
        parent.config = {}

        child1 = _CreateItem( declaration_type=Item.DeclarationType.Object,
                              parent=parent,
                            )
        child1.name = "child1"

        child2 = _CreateItem( declaration_type=Item.DeclarationType.Declaration,
                              parent=parent,
                            )
        child2.name = "child2"
        child2.reference = "child1"

        root = Resolve(parent, _CreatePlugin())

        self.assertEqual(len(root.items), 2)
        self.assertEqual(root.items[0].name, "child1")
        self.assertEqual(root.items[1].name, "child2")
        self.assertEqual(root.items[1].reference, root.items[0])
        self.assertEqual(root.items[1].element_type, Elements.ReferenceElement)
        
    # ----------------------------------------------------------------------
    def test_DoesNotExist(self):
        parent = _CreateItem()
        parent.config = {}

        child1 = _CreateItem( declaration_type=Item.DeclarationType.Declaration,
                              parent=parent,
                            )
        child1.name = "child1"
        child1.reference = "does_not_exist"
        
        self.assertRaises(Exceptions.ResolveInvalidReferenceException, lambda: Resolve(parent, _CreatePlugin()))

# ----------------------------------------------------------------------
class MetadataSuite(unittest.TestCase):
    # ----------------------------------------------------------------------
    def test_Name(self):
        parent = _CreateItem()
        parent.config = {}

        child1 = _CreateItem( declaration_type=Item.DeclarationType.Declaration,
                              parent=parent,
                            )
        child1.name = "this_should_be_overridden"
        child1.reference = "string"
        child1.metadata.Values["name"] = MetadataValue( "new_name",
                                                        MetadataSource.Explicit,
                                                        "<source>",
                                                        1,
                                                        2,
                                                      )

        root = Resolve(parent, _CreatePlugin())

        self.assertEqual(len(root.items), 1)
        self.assertEqual(root.items[0].name, "new_name")
        self.assertTrue("name" not in root.items[0].metadata.Values)

    # ----------------------------------------------------------------------
    def test_NamePluralConversion(self):
        parent = _CreateItem()
        parent.config = {}

        child1 = _CreateItem( declaration_type=Item.DeclarationType.Declaration,
                              parent=parent,
                            )
        child1.name = "this_should_be_overridden"
        child1.reference = "string"
        child1.metadata.Values["name"] = MetadataValue( "new_name",
                                                        MetadataSource.Explicit,
                                                        "<source>",
                                                        1,
                                                        2,
                                                      )

        child1.arity = Arity(1, None)

        root = Resolve(parent, _CreatePlugin())
        
        self.assertEqual(len(root.items), 1)
        self.assertEqual(root.items[0].name, "new_names")
        self.assertTrue("name" not in root.items[0].metadata.Values)
        
    # ----------------------------------------------------------------------
    def test_InvalidName(self):
        parent = _CreateItem()
        parent.config = {}

        child1 = _CreateItem( declaration_type=Item.DeclarationType.Declaration,
                              parent=parent,
                            )
        child1.name = "this_should_be_overridden"
        child1.reference = "string"
        child1.metadata.Values["name"] = MetadataValue( "",
                                                        MetadataSource.Explicit,
                                                        "<source>",
                                                        1,
                                                        2,
                                                      )

        self.assertRaises(Exceptions.ResolveInvalidCustomNameException, lambda: Resolve(parent, _CreatePlugin()))

    # ----------------------------------------------------------------------
    def test_Plural(self):
        parent = _CreateItem()
        parent.config = {}

        child1 = _CreateItem( declaration_type=Item.DeclarationType.Declaration,
                              parent=parent,
                            )
        child1.name = "this_should_be_overridden"
        child1.reference = "string"
        child1.arity = Arity(1, None)

        child1.metadata.Values["plural"] = MetadataValue( "items",
                                                          MetadataSource.Explicit,
                                                          "<source>",
                                                          1,
                                                          2,
                                                        )

        root = Resolve(parent, _CreatePlugin())

        self.assertEqual(len(root.items), 1)
        self.assertEqual(root.items[0].name, "items")

    # ----------------------------------------------------------------------
    def test_InvalidPlural(self):
        parent = _CreateItem()
        parent.config = {}

        child1 = _CreateItem( declaration_type=Item.DeclarationType.Declaration,
                              parent=parent,
                            )
        child1.name = "this_should_be_overridden"
        child1.reference = "string"
        child1.arity = Arity(1, None)

        child1.metadata.Values["plural"] = MetadataValue( "",
                                                          MetadataSource.Explicit,
                                                          "<source>",
                                                          1,
                                                          2,
                                                        )

        self.assertRaises(Exceptions.ResolveInvalidCustomNameException, lambda: Resolve(parent, _CreatePlugin()))

    # ----------------------------------------------------------------------
    def test_Optional(self):
        parent = _CreateItem()
        parent.config = {}

        child1 = _CreateItem( declaration_type=Item.DeclarationType.Declaration,
                              parent=parent,
                            )
        child1.name = "item"
        child1.reference = "string"
        child1.arity = Arity(0, 1)

        root = Resolve(parent, _CreatePlugin())

        self.assertEqual(len(root.items), 1)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _CreateItem( declaration_type=Item.DeclarationType.Object,
                 item_type=Item.ItemType.Standard,
                 parent=None,
                 source="<source>",
                 line=1,
                 column=1,
                 is_external=False,
               ):
    result = Item( declaration_type,
                   item_type,
                   parent,
                   source,
                   line,
                   column,
                   is_external,
                 )
    result.metadata = Metadata({}, "<source>", 0, 0)

    if parent:
        result.parent = parent
        parent.items.append(result)

    return result

# ----------------------------------------------------------------------
def _CreatePlugin( name="Plugin",
                   flags=ParseFlag.AllFlags,
                 ):
    # ----------------------------------------------------------------------
    class Object(object):
        pass

    # ----------------------------------------------------------------------

    plugin = Object()

    plugin.Name = name
    plugin.Description = "Plugin Description"
    plugin.Flags = flags
    plugin.BreaksReferenceChain = lambda item: False

    return plugin

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
