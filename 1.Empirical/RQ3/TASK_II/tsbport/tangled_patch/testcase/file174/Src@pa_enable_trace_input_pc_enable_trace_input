static int enable_trace_input(struct flb_hs *hs, const char *name, const char *prefix, const char *output_name, struct mk_list *props)
{
    struct flb_input_instance *in;


    in = find_input(hs, name);
    if (in == NULL) {
        return 404;
    }

    flb_chunk_trace_context_new(in, output_name, prefix, NULL, props);
    return (in->chunk_trace_ctxt == NULL ? 503 : 0);
}
