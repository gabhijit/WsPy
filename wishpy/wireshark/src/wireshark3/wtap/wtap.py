from cffi import FFI

from ...glib.glib_h import glib_h_cdef
from ...glib.garray_h import garray_h_cdef
from ...glib.glist_h import glist_h_cdef

from ...wsutil.nstime_h import wsutil_nstime_h_types_cdef
from ...wsutil.buffer_h import wsutil_buffer_h_cdef
from ...wsutil.inet_ipv4_h import wsutil_inet_ipv4_h_cdef
from ...wsutil.inet_ipv6_h import wsutil_inet_ipv6_h_cdef
from ...wsutil.inet_addr_h import wsutil_inet_addr_h_cdef

from .wtap_h import wtap_h_types_cdef, wtap_h_funcs_cdef
from .wtap_opttypes_h import (
        wtap_opttypes_h_types_cdef,
        wtap_opttypes_h_funcs_cdef)

#from ...ws_symbols_h import ws_symbols_h_cdef

wtap_ffi = FFI()

#wtap_ffi.cdef(ws_symbols_h_cdef)
# Get the definitions from glib
wtap_ffi.cdef(glib_h_cdef)
wtap_ffi.cdef(garray_h_cdef)
wtap_ffi.cdef(glist_h_cdef)


wtap_ffi.cdef(wsutil_nstime_h_types_cdef)
wtap_ffi.cdef(wsutil_buffer_h_cdef)
wtap_ffi.cdef(wsutil_inet_ipv4_h_cdef)
wtap_ffi.cdef(wsutil_inet_ipv6_h_cdef)
wtap_ffi.cdef(wsutil_inet_addr_h_cdef)

# Get the definitions from our on library
wtap_ffi.cdef(wtap_opttypes_h_types_cdef)
wtap_ffi.cdef(wtap_opttypes_h_funcs_cdef)
wtap_ffi.cdef(wtap_h_types_cdef)
wtap_ffi.cdef(wtap_h_funcs_cdef)

_pkg_name = 'wishpy.wireshark.lib.wtap3_ext'

_sources = '''
        #define HAVE_PLUGINS 1
        #include <wireshark/ws_symbol_export.h>
        #include <wireshark/wiretap/wtap.h>
        #include <wireshark/wsutil/privileges.h>
'''

_libraries = ['glib-2.0', 'wireshark', 'wsutil', 'wiretap']
_extra_compile_args = ['-I/usr/local/include/wireshark',
        '-I/usr/include/glib-2.0',
        '-I/usr/lib/x86_64-linux-gnu/glib-2.0/include']
_extra_link_args = ['-L/usr/local/lib']

wtap_ffi.set_source(_pkg_name,
        _sources,
        libraries=_libraries,
        extra_compile_args=_extra_compile_args,
        extra_link_args=_extra_link_args)
