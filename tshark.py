import os
import sys
import time
from datetime import datetime as dt

from wspy.wireshark.lib.epan_ext import lib as epan_lib
from wspy.wireshark.lib.epan_ext import ffi as epan_ffi

from wspy.wireshark.lib.wtap_ext import lib as wtap_lib
from wspy.wireshark.lib.wtap_ext import ffi as wtap_ffi
hfbases = {
        epan_lib.BASE_DEC : '{:d}',
        epan_lib.BASE_HEX : '0x{:x}',
        epan_lib.BASE_OCT : '{:o}',
        epan_lib.BASE_DEC_HEX: '{:d}(0x{:x})',
        epan_lib.BASE_HEX_DEC: '0x{:x}({:d})',
        epan_lib.BASE_PT_TCP: '{:d}',
        epan_lib.BASE_PT_UDP: '{:d}'

        }
def func_not_supported(*args):
    return "Not Supported"

def get_uinteger(hfinfo, fvalue):
    try:
        base_format = hfbases[hfinfo.display]
    except:
        return "Not Supported"

    return base_format.format(fvalue.value.uinteger,
            fvalue.value.uinteger)


fvalue_print_map = {
        epan_lib.FT_NONE: func_not_supported,
        epan_lib.FT_PROTOCOL: func_not_supported,
        epan_lib.FT_BOOLEAN: func_not_supported,
        epan_lib.FT_UINT8: get_uinteger,
        epan_lib.FT_UINT16: get_uinteger,
        epan_lib.FT_UINT32: get_uinteger,
        epan_lib.FT_INT16: func_not_supported,
        epan_lib.FT_INT32: func_not_supported,
        epan_lib.FT_ABSOLUTE_TIME: func_not_supported,
        epan_lib.FT_RELATIVE_TIME: func_not_supported,
        epan_lib.FT_STRING: func_not_supported,
        epan_lib.FT_ETHER: func_not_supported,
        epan_lib.FT_BYTES: func_not_supported,
        epan_lib.FT_IPv4: func_not_supported,
        epan_lib.FT_FRAMENUM: func_not_supported,
        }


@epan_ffi.callback('void(proto_node *, gpointer)')
def per_node_func(node_ptr, data_ptr):

    if data_ptr == epan_ffi.NULL:
        level = 0
    else:
        level = epan_ffi.cast('int *', data_ptr)[0]

    node = node_ptr[0]
    slash_tees = "\t" * (level)
    finfo = node.finfo
    hfinfo = finfo.hfinfo[0]
    print(slash_tees,
            epan_ffi.string(hfinfo.abbrev),
            hfinfo.display,
            #hfinfo.type,
            #finfo.length,
            #finfo.start,
            fvalue_print_map[hfinfo.type](hfinfo, finfo.value))

    child = node.first_child
    data_ptr_new = epan_ffi.new('int *')
    data_ptr_new[0] = level + 1
    while child != epan_ffi.NULL:
        per_node_func(child, epan_ffi.cast('void *', data_ptr_new))
        child = child.next

    #while child != epan_ffi.NULL:
    #    print("\t",
    #            epan_ffi.string(child.finfo.hfinfo[0].abbrev),
    #            child.finfo.hfinfo[0].type,
    #            child.finfo.hfinfo[0].display,
    #            child.finfo.value)
    #    child = child.next

def wtap_open_file_offline(filepath):
    """
    Opens a file given by filepath  using `wtap_open_offline` and returns a tuple containing
    Handle and file type.
    """

    if not os.path.exists(filepath):
        return None, None


    wtap_lib.wtap_init(False)

    # Open a wtap file
    err = wtap_ffi.new('int *')
    err_str = wtap_ffi.new("gchar *[256]")
    filename = filepath
    open_type = wtap_lib.WTAP_TYPE_AUTO
    wth = wtap_lib.wtap_open_offline(filename.encode(), open_type, err, err_str, False)
    if wth is wtap_ffi.NULL:
        return None, None

    wtap_file_type = wtap_lib.wtap_file_type_subtype(wth)
    return wth, wtap_file_type

# Open `epan_lib`

def epan_lib_init():
    """
    Performs initialzation of the `epan` library. Calls
    1. `init_process_policies` (Required)
    2. `epan_init` (Required)
    3. `epan_load_settings` (Required)

    Returns True/False based upon result of operation.
    """

    epan_lib.init_process_policies()
    null_register_cb = epan_ffi.cast('register_cb', epan_ffi.NULL)
    register_protocols_handle = epan_ffi.callback('void (*)(register_cb, gpointer)',
            epan_lib.register_all_protocols)
    register_handoffs_handle = epan_ffi.callback('void (*)(register_cb, gpointer)',
            epan_lib.register_all_protocol_handoffs)
    result = epan_lib.epan_init(
            register_protocols_handle,
            register_handoffs_handle,
            null_register_cb, epan_ffi.NULL)
    if result:
        epan_lib.epan_load_settings()

    return result

def epan_perform_dissection(wth, wth_file_type):
    """
    Performs dissection of the file bound to `wth`
    """
    empty_packet_provider_funcs = epan_ffi.new('struct packet_provider_funcs *')
    epan_session = epan_lib.epan_new(epan_ffi.NULL, empty_packet_provider_funcs)

    # TODO: make proper `epan_session` for us
    epan_dissect_obj = epan_lib.epan_dissect_new(epan_session, True, True)

    offset = wtap_ffi.new('gint64 *')
    frame_data_ref = epan_ffi.new('frame_data **')
    elapsed_time_ptr = epan_ffi.new('nstime_t *')

    err = wtap_ffi.new('int *')
    err_str = wtap_ffi.new("gchar **")

    frame_data_ref[0] = epan_ffi.NULL
    frame_data_ptr = epan_ffi.new('frame_data *')
    cum_bytes = epan_ffi.new('guint32 *')
    then = dt.now()
    processed = 0
    while True:
        result = wtap_lib.wtap_read(wth, err, err_str, offset)

        if result == True:
            processed += 1
            rec = wtap_lib.wtap_get_rec(wth)
            buf_ptr = wtap_lib.wtap_get_buf_ptr(wth)

            epan_rec = epan_ffi.cast('wtap_rec *', rec)
            pkt_len = rec.rec_header.packet_header.len
            pkt_reported_len = rec.rec_header.packet_header.caplen


            # FIXME: `Let there be proper `offset`, `cum_bytes`
            epan_lib.frame_data_init(frame_data_ptr, 0, epan_rec,
                    offset[0], cum_bytes[0])

            # FIXME: Look at properly using `frame_data_ref`
            epan_lib.frame_data_set_before_dissect(frame_data_ptr,
                    elapsed_time_ptr, frame_data_ref, epan_ffi.NULL)


            # Not sure what this is - Just copied from `tshark` sources
            epan_lib.prime_epan_dissect_with_postdissector_wanted_hfids(
                    epan_dissect_obj)

            ## Do actual dissection here.
            # Get buffer and tvbuff first and then run dissector
            tvb_ptr = epan_lib.tvb_new_real_data(buf_ptr, pkt_len,
                    pkt_reported_len)

            epan_lib.epan_dissect_run(epan_dissect_obj, wth_file_type,
                    epan_rec, tvb_ptr, frame_data_ptr, epan_ffi.NULL)

            # FIXME: Add code that gets our `packet` structure here
            epan_lib.proto_tree_children_foreach(epan_dissect_obj[0].tree,
                    per_node_func, epan_ffi.NULL)

            # Reset the frame data and dissector object
            epan_lib.frame_data_set_after_dissect(frame_data_ptr, cum_bytes)
            epan_lib.epan_dissect_reset(epan_dissect_obj)

        else:
            break

    now = dt.now()

    print("Processded {} packets in {}".format(processed, (now - then)))


if __name__ == '__main__':

    if not len(sys.argv) >= 2:
        print("Usage: tshark.py <filepath>")
        sys.exit(1)

    input_filepath = sys.argv[1]

    wth, wth_ftype = wtap_open_file_offline(input_filepath)
    if wth is None:
        print("Unable to get 'wiretap' File Handle.")
        sys.exit(1)

    epan_lib_result = epan_lib_init()
    if not epan_lib_result:
        print("Unable to open 'epan' library.")
        sys.exit(1)

    epan_perform_dissection(wth, wth_ftype)
