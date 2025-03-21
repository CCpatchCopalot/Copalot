int api_v1_trace(struct flb_hs *hs)
{
    if (hs->config->enable_chunk_trace == FLB_TRUE) {
        mk_vhost_handler(hs->ctx, hs->vid, "/api/v1/traces/", cb_traces, hs);
        mk_vhost_handler(hs->ctx, hs->vid, "/api/v1/trace/*", cb_trace, hs);
    }
    return 0;
}
