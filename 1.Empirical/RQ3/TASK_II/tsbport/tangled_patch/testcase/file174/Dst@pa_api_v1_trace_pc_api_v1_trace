int api_v1_trace(struct flb_hs *hs)
{
    mk_vhost_handler(hs->ctx, hs->vid, "/api/v1/traces/", cb_traces, hs);
    mk_vhost_handler(hs->ctx, hs->vid, "/api/v1/trace/*", cb_trace, hs);
    return 0;
}
