static void cb_trace(mk_request_t *request, void *data)
{
    flb_sds_t out_buf;
    msgpack_sbuffer mp_sbuf;
    msgpack_packer mp_pck;
    int response = 404;
    flb_sds_t input_name = NULL;


    /* initialize buffers */
    msgpack_sbuffer_init(&mp_sbuf);
    msgpack_packer_init(&mp_pck, &mp_sbuf, msgpack_sbuffer_write);

    input_name = get_input_name(request);
    if (input_name == NULL) {
        response = 404;
        goto error;
    }

    if (request->method == MK_METHOD_POST || request->method == MK_METHOD_GET) {
        response = http_enable_trace(request, data, input_name, flb_sds_len(input_name), &mp_pck);
    }
    else if (request->method == MK_METHOD_DELETE) {
        response = http_disable_trace(request, data, input_name, flb_sds_len(input_name), &mp_pck);
    }
error:
    if (response == 404) {
        msgpack_pack_map(&mp_pck, 1);
        msgpack_pack_str_with_body(&mp_pck, HTTP_FIELD_STATUS, HTTP_FIELD_STATUS_LEN);
        msgpack_pack_str_with_body(&mp_pck, HTTP_RESULT_NOTFOUND, HTTP_RESULT_NOTFOUND_LEN);
    }
    else if (response == 503) {
        msgpack_pack_map(&mp_pck, 1);
        msgpack_pack_str_with_body(&mp_pck, HTTP_FIELD_STATUS, HTTP_FIELD_STATUS_LEN);
        msgpack_pack_str_with_body(&mp_pck, HTTP_RESULT_ERROR, HTTP_RESULT_ERROR_LEN);
    }

    if (input_name != NULL) {
        flb_sds_destroy(input_name);
    }

    /* Export to JSON */
    out_buf = flb_msgpack_raw_to_json_sds(mp_sbuf.data, mp_sbuf.size);
    if (out_buf == NULL) {
        mk_http_status(request, 503);
        mk_http_done(request);
        return;
    }

    mk_http_status(request, response);
    mk_http_send(request, out_buf, flb_sds_len(out_buf), NULL);
    mk_http_done(request);

    msgpack_sbuffer_destroy(&mp_sbuf);
    flb_sds_destroy(out_buf);
}
