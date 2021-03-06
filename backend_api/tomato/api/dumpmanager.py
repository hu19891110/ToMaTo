# -*- coding: utf-8 -*-
# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from api_helpers import getCurrentUserInfo
from ..lib.service import get_backend_debug_proxy

def errordump_info(group_id, source, dump_id, include_data=False):
    """
    Returns details for the given dump.
    A dump is identified by its group_id, its source, and the dump_id on this source.
    
    Parameter *group_id*:
      A string. This is the group id of the dump group.

    Parameter *source*:
      A string. This is the source (i.e., a certain host, or the backend) of the dump.
    
    Parameter *dump_id*: 
      The unique identifier of the dump to be queried. 
    
    Parameter *include_data*:
      A boolean.
      Every dump has environment data attached to it. This data may be big (i.e., >1MB).
      By default, the data of a dump has most likely not been loaded from its source.
      If include_data is False, this data will not be returned by this call.
      If it is True, this data will first be fetched from the source, if needed, and included in this call's return.
    
    Return value:
      The return value of this method is the info dict of the dump.
      If include_data is True, it will contain a data field, otherwise a data_available indicator.
    """
    getCurrentUserInfo().check_may_view_debugging_info()
    return get_backend_debug_proxy().errordump_info(group_id, source, dump_id, include_data)

def errordump_list(group_id, source=None):
    """
    Returns a list of dumps.
    
    Parameter *group_id*: 
      A string. Only dumps of this group will be included.
    
    Parameter *source*:
      A string. If this is not None, only dumps from this source will be included.
    
    Parameter *data_available*:
      A boolean. If this is not None, only dumps which match this criterion will be included. 
      
    Return value:
      A list of dumps, filtered by the arguments.
    """
    getCurrentUserInfo().check_may_view_debugging_info()
    return get_backend_debug_proxy().errordump_list(group_id, source)

def errorgroup_info(group_id, include_dumps=False):
    """
    Returns details for the given dump group.
    
    Parameter *group_id*:
      A string. The unique identifier of the group.
    
    Parameter *include_dumps*: 
      If true, a list of all dumps will be attached. 
    
    Return value:
      The return value of this method is the info dict of the group, maybe expanded by a list of dumps.
    """
    getCurrentUserInfo().check_may_view_debugging_info()
    return get_backend_debug_proxy().errorgroup_info(group_id, include_dumps, as_user=getCurrentUserInfo().get_username())

def errorgroup_list(show_empty=False):
    """
    Returns a list of all error groups.
    """
    getCurrentUserInfo().check_may_view_debugging_info()
    return get_backend_debug_proxy().errorgroup_list(show_empty, as_user=getCurrentUserInfo().get_username())

def errorgroup_modify(group_id, attrs):
    """
    Allows to modify the description of the error group.
    
    Parameter *group_id*:
      A string. The unique identifier of the group.
    
    Parameter *attrs*: 
      A dict with attributes to update. This matches the info dict.
      Only the description can be updated. 
    
    Return value:
      The return value of this method is the info dict of the group.
    """
    getCurrentUserInfo().check_may_view_debugging_info()
    return get_backend_debug_proxy().errorgroup_modify(group_id, attrs)

def errorgroup_remove(group_id):
    """
    Remove a dump.
    
    Parameter *dump_id*: 
      The unique identifier of the group to be removed.
    """
    getCurrentUserInfo().check_may_view_debugging_info()
    get_backend_debug_proxy().errorgroup_remove(group_id)

def errordumps_force_refresh():
    """
    Force a refresh of dumps.
    This is done automatically in a longer interval.
    To get instant access to all dumps, call this function.
    
    Return value:
      The time in seconds it takes until all dumps should be collected.
    """
    getCurrentUserInfo().check_may_view_debugging_info()
    return get_backend_debug_proxy().errordumps_force_refresh()

def errorgroup_hide(group_id):
    """
    Hide an errorgroup.
    It will be shown as soon as a new dump is inserted.

    :param group_id: the group ID
    :return: None
    """
    getCurrentUserInfo().check_may_view_debugging_info()
    get_backend_debug_proxy().errorgroup_hide(group_id)

def errorgroup_favorite(group_id, is_favorite):
    """
    Add or remove the group to favorites of the current user

    :param group_id: group to add/remove
    :param is_favorite: True to add, False to remove.
    :return: None
    """
    getCurrentUserInfo().check_may_view_debugging_info()
    get_backend_debug_proxy().errorgroup_favorite(getCurrentUserInfo().get_username(), group_id, is_favorite)
