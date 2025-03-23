GF_Err chnl_box_size(GF_Box *s)
{
	GF_ChannelLayoutBox *ptr = (GF_ChannelLayoutBox *) s;
	s->size += 1;
	if (ptr->version==1) s->size++;
	if (ptr->layout.stream_structure & 1) {
		s->size += 1;
		if (ptr->layout.definedLayout==0) {
			u32 i;
			if (ptr->version==1) s->size++;
			for (i=0; i<ptr->layout.channels_count; i++) {
				s->size+=1;
				if (ptr->layout.layouts[i].position==126)
					s->size+=3;
			}
		} else {
			if (ptr->version==1) {
				s->size += 1;
				if (ptr->layout.omitted_channels_present)
					s->size += 8;
			} else {
				s->size += 8;
			}
		}
	}
	if ((ptr->version==0) && (ptr->layout.stream_structure & 2)) {
		s->size += 1;
	}
	return GF_OK;
}
