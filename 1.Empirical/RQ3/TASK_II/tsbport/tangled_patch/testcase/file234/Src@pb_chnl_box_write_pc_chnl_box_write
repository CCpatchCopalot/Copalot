GF_Err chnl_box_write(GF_Box *s, GF_BitStream *bs)
{
	GF_Err e;
	GF_ChannelLayoutBox *ptr = (GF_ChannelLayoutBox *) s;

	e = gf_isom_full_box_write(s, bs);
	if (e) return e;

	gf_bs_write_u8(bs, ptr->layout.stream_structure);
	if (ptr->version==0) {
		gf_bs_write_u8(bs, ptr->layout.stream_structure);
	} else {
		gf_bs_write_int(bs, ptr->layout.stream_structure, 4);
		gf_bs_write_int(bs, ptr->layout.format_ordering, 4);
		gf_bs_write_u8(bs, ptr->layout.base_channel_count);
	}
	if (ptr->layout.stream_structure & 1) {
		gf_bs_write_u8(bs, ptr->layout.definedLayout);
		if (ptr->layout.definedLayout==0) {
			u32 i;
			if (ptr->version==1) {
				gf_bs_write_u8(bs, ptr->layout.channels_count);
			}
			for (i=0; i<ptr->layout.channels_count; i++) {
				gf_bs_write_u8(bs, ptr->layout.layouts[i].position);
				if (ptr->layout.layouts[i].position==126) {
					gf_bs_write_int(bs, ptr->layout.layouts[i].azimuth, 16);
					gf_bs_write_int(bs, ptr->layout.layouts[i].elevation, 8);
				}
			}
		} else {
			if (ptr->version==1) {
				gf_bs_write_int(bs, 0, 4);
				gf_bs_write_int(bs, ptr->layout.channel_order_definition, 3);
				gf_bs_write_int(bs, ptr->layout.omitted_channels_present, 1);
				if (ptr->layout.omitted_channels_present)
					gf_bs_write_u64(bs, ptr->layout.omittedChannelsMap);
			} else {
				gf_bs_write_u64(bs, ptr->layout.omittedChannelsMap);
			}
		}
	}
	if ((ptr->version==0) && (ptr->layout.stream_structure & 2)) {
		gf_bs_write_u8(bs, ptr->layout.object_count);
	}
	return GF_OK;
}
