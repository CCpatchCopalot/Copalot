GF_Err iods_box_read(GF_Box *s, GF_BitStream *bs)
{
	GF_Err e;
	u32 descSize;
	char *desc;
	GF_ObjectDescriptorBox *ptr = (GF_ObjectDescriptorBox *)s;

	//use the OD codec...
	descSize = (u32) (ptr->size);
	desc = (char*)gf_malloc(sizeof(char) * descSize);
	if (!desc) return GF_OUT_OF_MEM;

	gf_bs_read_data(bs, desc, descSize);
	e = gf_odf_desc_read(desc, descSize, &ptr->descriptor);
	//OK, free our desc
	gf_free(desc);

	if (e) return e;
	switch (ptr->descriptor->tag) {
	case GF_ODF_ISOM_OD_TAG:
	case GF_ODF_ISOM_IOD_TAG:
		break;
	default:
		GF_LOG(GF_LOG_ERROR, GF_LOG_CONTAINER, ("[iso file] Invalid descriptor in iods, tag %u found but only %u or %u allowed\n", ptr->descriptor->tag, GF_ODF_ISOM_IOD_TAG, GF_ODF_ISOM_OD_TAG ));
		return GF_ISOM_INVALID_FILE;
	}
	return GF_OK;
}
