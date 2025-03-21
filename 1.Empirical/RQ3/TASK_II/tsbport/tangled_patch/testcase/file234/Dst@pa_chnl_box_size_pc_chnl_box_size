GF_Err chnl_box_size(GF_Box *s)
{
	GF_ChannelLayoutBox *ptr = (GF_ChannelLayoutBox *) s;
	s->size += 1;
	if (ptr->layout.stream_structure & 1) {
		s->size += 1;
		if (ptr->layout.definedLayout==0) {
			u32 i;
			for (i=0; i<ptr->layout.channels_count; i++) {
				s->size+=1;
				if (ptr->layout.layouts[i].position==126)
					s->size+=3;
			}
		} else {
			s->size += 8;
		}
	}
	if (ptr->layout.stream_structure & 2) {
		s->size += 1;
	}
	return GF_OK;
}
