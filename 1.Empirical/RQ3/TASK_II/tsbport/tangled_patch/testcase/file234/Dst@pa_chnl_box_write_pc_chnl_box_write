GF_Err chnl_box_write(GF_Box *s, GF_BitStream *bs)
{
	GF_Err e;
	GF_ChannelLayoutBox *ptr = (GF_ChannelLayoutBox *) s;

	e = gf_isom_full_box_write(s, bs);
	if (e) return e;

	gf_bs_write_u8(bs, ptr->layout.stream_structure);
	if (ptr->layout.stream_structure & 1) {
		gf_bs_write_u8(bs, ptr->layout.definedLayout);
		if (ptr->layout.definedLayout==0) {
			u32 i;
			for (i=0; i<ptr->layout.channels_count; i++) {
				gf_bs_write_u8(bs, ptr->layout.layouts[i].position);
				if (ptr->layout.layouts[i].position==126) {
					gf_bs_write_int(bs, ptr->layout.layouts[i].azimuth, 16);
					gf_bs_write_int(bs, ptr->layout.layouts[i].elevation, 8);
				}
			}
		} else {
			gf_bs_write_u64(bs, ptr->layout.omittedChannelsMap);
		}
	}
	if (ptr->layout.stream_structure & 2) {
		gf_bs_write_u8(bs, ptr->layout.object_count);
	}
	return GF_OK;
}
