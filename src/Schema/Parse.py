# ----------------------------------------------------------------------
# |  
# |  Parse.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-09 13:16:09
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Functionality used when parsing SimpleSchema files"""

import os

from collections import OrderedDict

import six

import CommonEnvironment

from .Impl.Populate import Populate
from .Impl.Resolve import Resolve
from .Impl.Validate import Validate
from .Impl.Transform import Transform

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
def ParseFiles( filenames,
                plugin,
                filter_unsupported_extensions,
                filter_unsupported_attributes,
              ):
    file_map = OrderedDict()

    for filename in filenames:
        file_map[filename] = lambda filename=filename: open(filename).read()

    return ParseEx( file_map,
                    plugin,
                    filter_unsupported_extensions,
                    filter_unsupported_attributes,
                  )

# ----------------------------------------------------------------------
def ParseStrings( named_strings,            # { "<name>" : "<content>", ... }
                  plugin,
                  filter_unsupported_extensions,
                  filter_unsupported_attributes,
                ):
    string_map = OrderedDict()

    for k, v in six.iteritems(named_strings):
        string_map[k] = lambda v=v: v

    return ParseEx( string_map,
                    plugin,
                    filter_unsupported_extensions,
                    filter_unsupported_attributes,
                  )

# ----------------------------------------------------------------------
def ParseEx( source_name_content_generators,            # { "<name>" : def Func() -> content }
             plugin,
             filter_unsupported_extensions,
             filter_unsupported_attributes,
           ):
    plugin.VerifyFlags()

    root = Populate(source_name_content_generators, plugin.Flags)
    root = Resolve(root, plugin)

    root = Validate( root,
                     plugin,
                     filter_unsupported_extensions,
                     filter_unsupported_attributes,
                   )

    root = Transform(root, plugin)

    # Eliminate the root element as the parent for top-level elements
    for child in root.Children:
        child.Parent = None

    return root.Children
