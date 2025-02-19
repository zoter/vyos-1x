# configtree -- a standalone VyOS config file manipulation library (Python bindings)
# Copyright (C) 2018-2022 VyOS maintainers and contributors
#
# This library is free software; you can redistribute it and/or modify it under the terms of
# the GNU Lesser General Public License as published by the Free Software Foundation;
# either version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along with this library;
# if not, write to the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import os
import re
import json

from ctypes import cdll, c_char_p, c_void_p, c_int, c_bool

LIBPATH = '/usr/lib/libvyosconfig.so.0'

def escape_backslash(string: str) -> str:
    """Escape single backslashes in string that are not in escape sequence"""
    p = re.compile(r'(?<!\\)[\\](?!b|f|n|r|t|\\[^bfnrt])')
    result = p.sub(r'\\\\', string)
    return result

def extract_version(s):
    """ Extract the version string from the config string """
    t = re.split('(^//)', s, maxsplit=1, flags=re.MULTILINE)
    return (s, ''.join(t[1:]))

def check_path(path):
    # Necessary type checking
    if not isinstance(path, list):
        raise TypeError("Expected a list, got a {}".format(type(path)))
    else:
        pass


class ConfigTreeError(Exception):
    pass


class ConfigTree(object):
    def __init__(self, config_string=None, address=None, libpath=LIBPATH):
        if config_string is None and address is None:
            raise TypeError("ConfigTree() requires one of 'config_string' or 'address'")
        self.__config = None
        self.__lib = cdll.LoadLibrary(libpath)

        # Import functions
        self.__from_string = self.__lib.from_string
        self.__from_string.argtypes = [c_char_p]
        self.__from_string.restype = c_void_p

        self.__get_error = self.__lib.get_error
        self.__get_error.argtypes = []
        self.__get_error.restype = c_char_p

        self.__to_string = self.__lib.to_string
        self.__to_string.argtypes = [c_void_p, c_bool]
        self.__to_string.restype = c_char_p

        self.__to_commands = self.__lib.to_commands
        self.__to_commands.argtypes = [c_void_p, c_char_p]
        self.__to_commands.restype = c_char_p

        self.__to_json = self.__lib.to_json
        self.__to_json.argtypes = [c_void_p]
        self.__to_json.restype = c_char_p

        self.__to_json_ast = self.__lib.to_json_ast
        self.__to_json_ast.argtypes = [c_void_p]
        self.__to_json_ast.restype = c_char_p

        self.__set_add_value = self.__lib.set_add_value
        self.__set_add_value.argtypes = [c_void_p, c_char_p, c_char_p]
        self.__set_add_value.restype = c_int

        self.__delete_value = self.__lib.delete_value
        self.__delete_value.argtypes = [c_void_p, c_char_p, c_char_p]
        self.__delete_value.restype = c_int

        self.__delete = self.__lib.delete_node
        self.__delete.argtypes = [c_void_p, c_char_p]
        self.__delete.restype = c_int

        self.__rename = self.__lib.rename_node
        self.__rename.argtypes = [c_void_p, c_char_p, c_char_p]
        self.__rename.restype = c_int

        self.__copy = self.__lib.copy_node
        self.__copy.argtypes = [c_void_p, c_char_p, c_char_p]
        self.__copy.restype = c_int

        self.__set_replace_value = self.__lib.set_replace_value
        self.__set_replace_value.argtypes = [c_void_p, c_char_p, c_char_p]
        self.__set_replace_value.restype = c_int

        self.__set_valueless = self.__lib.set_valueless
        self.__set_valueless.argtypes = [c_void_p, c_char_p]
        self.__set_valueless.restype = c_int

        self.__exists = self.__lib.exists
        self.__exists.argtypes = [c_void_p, c_char_p]
        self.__exists.restype = c_int

        self.__list_nodes = self.__lib.list_nodes
        self.__list_nodes.argtypes = [c_void_p, c_char_p]
        self.__list_nodes.restype = c_char_p

        self.__return_value = self.__lib.return_value
        self.__return_value.argtypes = [c_void_p, c_char_p]
        self.__return_value.restype = c_char_p

        self.__return_values = self.__lib.return_values
        self.__return_values.argtypes = [c_void_p, c_char_p]
        self.__return_values.restype = c_char_p

        self.__is_tag = self.__lib.is_tag
        self.__is_tag.argtypes = [c_void_p, c_char_p]
        self.__is_tag.restype = c_int

        self.__set_tag = self.__lib.set_tag
        self.__set_tag.argtypes = [c_void_p, c_char_p]
        self.__set_tag.restype = c_int

        self.__get_subtree = self.__lib.get_subtree
        self.__get_subtree.argtypes = [c_void_p, c_char_p]
        self.__get_subtree.restype = c_void_p

        self.__destroy = self.__lib.destroy
        self.__destroy.argtypes = [c_void_p]

        if address is None:
            config_section, version_section = extract_version(config_string)
            config_section = escape_backslash(config_section)
            config = self.__from_string(config_section.encode())
            if config is None:
                msg = self.__get_error().decode()
                raise ValueError("Failed to parse config: {0}".format(msg))
            else:
                self.__config = config
                self.__version = version_section
        else:
            self.__config = address
            self.__version = ''

        self.__migration = os.environ.get('VYOS_MIGRATION')

    def __del__(self):
        if self.__config is not None:
            self.__destroy(self.__config)

    def __str__(self):
        return self.to_string()

    def _get_config(self):
        return self.__config

    def to_string(self, ordered_values=False):
        config_string = self.__to_string(self.__config, ordered_values).decode()
        config_string = "{0}\n{1}".format(config_string, self.__version)
        return config_string

    def to_commands(self, op="set"):
        return self.__to_commands(self.__config, op.encode()).decode()

    def to_json(self):
        return self.__to_json(self.__config).decode()

    def to_json_ast(self):
        return self.__to_json_ast(self.__config).decode()

    def set(self, path, value=None, replace=True):
        """Set new entry in VyOS configuration.
        path: configuration path e.g. 'system dns forwarding listen-address'
        value: value to be added to node, e.g. '172.18.254.201'
        replace: True: current occurance will be replaced
                 False: new value will be appended to current occurances - use
                 this for adding values to a multi node
        """

        check_path(path)
        path_str = " ".join(map(str, path)).encode()

        if value is None:
            self.__set_valueless(self.__config, path_str)
        else:
            if replace:
                self.__set_replace_value(self.__config, path_str, str(value).encode())
            else:
                self.__set_add_value(self.__config, path_str, str(value).encode())

        if self.__migration:
            print(f"- op: set path: {path} value: {value} replace: {replace}")

    def delete(self, path):
        check_path(path)
        path_str = " ".join(map(str, path)).encode()

        self.__delete(self.__config, path_str)

        if self.__migration:
            print(f"- op: delete path: {path}")

    def delete_value(self, path, value):
        check_path(path)
        path_str = " ".join(map(str, path)).encode()

        self.__delete_value(self.__config, path_str, value.encode())

        if self.__migration:
            print(f"- op: delete_value path: {path} value: {value}")

    def rename(self, path, new_name):
        check_path(path)
        path_str = " ".join(map(str, path)).encode()
        newname_str = new_name.encode()

        # Check if a node with intended new name already exists
        new_path = path[:-1] + [new_name]
        if self.exists(new_path):
            raise ConfigTreeError()
        res = self.__rename(self.__config, path_str, newname_str)
        if (res != 0):
            raise ConfigTreeError("Path [{}] doesn't exist".format(path))

        if self.__migration:
            print(f"- op: rename old_path: {path} new_path: {new_path}")

    def copy(self, old_path, new_path):
        check_path(old_path)
        check_path(new_path)
        oldpath_str = " ".join(map(str, old_path)).encode()
        newpath_str = " ".join(map(str, new_path)).encode()

        # Check if a node with intended new name already exists
        if self.exists(new_path):
            raise ConfigTreeError()
        res = self.__copy(self.__config, oldpath_str, newpath_str)
        if (res != 0):
            msg = self.__get_error().decode()
            raise ConfigTreeError(msg)

        if self.__migration:
            print(f"- op: copy old_path: {old_path} new_path: {new_path}")

    def exists(self, path):
        check_path(path)
        path_str = " ".join(map(str, path)).encode()

        res = self.__exists(self.__config, path_str)
        if (res == 0):
            return False
        else:
            return True

    def list_nodes(self, path):
        check_path(path)
        path_str = " ".join(map(str, path)).encode()

        res_json = self.__list_nodes(self.__config, path_str).decode()
        res = json.loads(res_json)

        if res is None:
            raise ConfigTreeError("Path [{}] doesn't exist".format(path_str))
        else:
            return res

    def return_value(self, path):
        check_path(path)
        path_str = " ".join(map(str, path)).encode()

        res_json = self.__return_value(self.__config, path_str).decode()
        res = json.loads(res_json)

        if res is None:
            raise ConfigTreeError("Path [{}] doesn't exist".format(path_str))
        else:
            return res

    def return_values(self, path):
        check_path(path)
        path_str = " ".join(map(str, path)).encode()

        res_json = self.__return_values(self.__config, path_str).decode()
        res = json.loads(res_json)

        if res is None:
            raise ConfigTreeError("Path [{}] doesn't exist".format(path_str))
        else:
            return res

    def is_tag(self, path):
        check_path(path)
        path_str = " ".join(map(str, path)).encode()

        res = self.__is_tag(self.__config, path_str)
        if (res >= 1):
            return True
        else:
            return False

    def set_tag(self, path):
        check_path(path)
        path_str = " ".join(map(str, path)).encode()

        res = self.__set_tag(self.__config, path_str)
        if (res == 0):
            return True
        else:
            raise ConfigTreeError("Path [{}] doesn't exist".format(path_str))

    def get_subtree(self, path, with_node=False):
        check_path(path)
        path_str = " ".join(map(str, path)).encode()

        res = self.__get_subtree(self.__config, path_str, with_node)
        subt = ConfigTree(address=res)
        return subt

def show_diff(left, right, path=[], commands=False, libpath=LIBPATH):
    if left is None:
        left = ConfigTree(config_string='\n')
    if right is None:
        right = ConfigTree(config_string='\n')
    if not (isinstance(left, ConfigTree) and isinstance(right, ConfigTree)):
        raise TypeError("Arguments must be instances of ConfigTree")
    if path:
        if (not left.exists(path)) and (not right.exists(path)):
            raise ConfigTreeError(f"Path {path} doesn't exist")

    check_path(path)
    path_str = " ".join(map(str, path)).encode()

    __lib = cdll.LoadLibrary(libpath)
    __show_diff = __lib.show_diff
    __show_diff.argtypes = [c_bool, c_char_p, c_void_p, c_void_p]
    __show_diff.restype = c_char_p
    __get_error = __lib.get_error
    __get_error.argtypes = []
    __get_error.restype = c_char_p

    res = __show_diff(commands, path_str, left._get_config(), right._get_config())
    res = res.decode()
    if res == "#1@":
        msg = __get_error().decode()
        raise ConfigTreeError(msg)

    return res

def union(left, right, libpath=LIBPATH):
    if left is None:
        left = ConfigTree(config_string='\n')
    if right is None:
        right = ConfigTree(config_string='\n')
    if not (isinstance(left, ConfigTree) and isinstance(right, ConfigTree)):
        raise TypeError("Arguments must be instances of ConfigTree")

    __lib = cdll.LoadLibrary(libpath)
    __tree_union = __lib.tree_union
    __tree_union.argtypes = [c_void_p, c_void_p]
    __tree_union.restype = c_void_p
    __get_error = __lib.get_error
    __get_error.argtypes = []
    __get_error.restype = c_char_p

    res = __tree_union( left._get_config(), right._get_config())
    tree = ConfigTree(address=res)

    return tree

def reference_tree_to_json(from_dir, to_file, libpath=LIBPATH):
    __lib = cdll.LoadLibrary(libpath)
    __reference_tree_to_json = __lib.reference_tree_to_json
    __reference_tree_to_json.argtypes = [c_char_p, c_char_p]
    __get_error = __lib.get_error
    __get_error.argtypes = []
    __get_error.restype = c_char_p

    res = __reference_tree_to_json(from_dir.encode(), to_file.encode())
    if res == 1:
        msg = __get_error().decode()
        raise ConfigTreeError(msg)

class DiffTree:
    def __init__(self, left, right, path=[], libpath=LIBPATH):
        if left is None:
            left = ConfigTree(config_string='\n')
        if right is None:
            right = ConfigTree(config_string='\n')
        if not (isinstance(left, ConfigTree) and isinstance(right, ConfigTree)):
            raise TypeError("Arguments must be instances of ConfigTree")
        if path:
            if not left.exists(path):
                raise ConfigTreeError(f"Path {path} doesn't exist in lhs tree")
            if not right.exists(path):
                raise ConfigTreeError(f"Path {path} doesn't exist in rhs tree")

        self.left = left
        self.right = right

        self.__lib = cdll.LoadLibrary(libpath)

        self.__diff_tree = self.__lib.diff_tree
        self.__diff_tree.argtypes = [c_char_p, c_void_p, c_void_p]
        self.__diff_tree.restype = c_void_p

        self.__trim_tree = self.__lib.trim_tree
        self.__trim_tree.argtypes = [c_void_p, c_void_p]
        self.__trim_tree.restype = c_void_p

        check_path(path)
        path_str = " ".join(map(str, path)).encode()

        res = self.__diff_tree(path_str, left._get_config(), right._get_config())

        # full diff config_tree and python dict representation
        self.full = ConfigTree(address=res)
        self.dict = json.loads(self.full.to_json())

        # config_tree sub-trees
        self.add = self.full.get_subtree(['add'])
        self.sub = self.full.get_subtree(['sub'])
        self.inter = self.full.get_subtree(['inter'])

        # trim sub(-tract) tree to get delete tree for commands
        ref = self.right.get_subtree(path, with_node=True) if path else self.right
        res = self.__trim_tree(self.sub._get_config(), ref._get_config())
        self.delete = ConfigTree(address=res)

    def to_commands(self):
        add = self.add.to_commands()
        delete = self.delete.to_commands(op="delete")
        return delete + "\n" + add
