static int disable_trace_input(struct flb_hs *hs, const char *name)
{
    struct flb_input_instance *in;
    

    in = find_input(hs, name);
    if (in == NULL) {
        return 404;
    }

    if (in->chunk_trace_ctxt != NULL) {
        flb_chunk_trace_context_destroy(in);
    }
    return 201;
}
