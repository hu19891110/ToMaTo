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

from ..lib.service import get_backend_core_proxy
from ..lib.cache import cached

@cached(3600*6)
def capabilities_element(type, host=None): #@ReservedAssignment
	return get_backend_core_proxy().capabilities_element(type, host)

@cached(3600*6)
def capabilities_connection(type, host=None): #@ReservedAssignment
	return get_backend_core_proxy().capabilities_connection(type, host)

@cached(3600*6)
def capabilities():
	return get_backend_core_proxy().capabilities()
