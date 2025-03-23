static u32 gf_m2ts_get_section_length(char byte0, char byte1, char byte2)
{
	u32 length;
	if (gf_m2ts_is_long_section(byte0)) {
		length = 3 + ( (((u8)byte1<<8) | (byte2&0xff)) & 0xfff );
	} else {
		length = 3 + ( (((u8)byte1<<8) | (byte2&0xff)) & 0x3ff );
	}
	return length;
}
