static int http_disable_trace(mk_request_t *request, void *data, const char *input_name, msgpack_packer *mp_pck)
{
    struct flb_hs *hs = data;
    int toggled_on = 503;


    toggled_on = disable_trace_input(hs, input_name);
    if (toggled_on < 300) {
        msgpack_pack_map(mp_pck, 1);
        msgpack_pack_str_with_body(mp_pck, "status", strlen("status"));
        msgpack_pack_str_with_body(mp_pck, "ok", strlen("ok"));
        return 201;
    }

    return toggled_on;
}
