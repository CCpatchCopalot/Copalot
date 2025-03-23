R_API bool r_anal_vtable_begin(RAnal *anal, RVTableContext *context) {
	context->anal = anal;
	context->abi = anal->cxxabi;
	context->word_size = (ut8) (anal->config->bits / 8);
	const bool is_arm = anal->cur->arch && r_str_startswith (anal->cur->arch, "arm");
	if (is_arm && context->word_size < 4) {
		context->word_size = 4;
	}
	const bool be = anal->config->big_endian;
	switch (context->word_size) {
	case 1:
		context->read_addr = be? vtable_read_addr_be8 : vtable_read_addr_le8;
		break;
	case 2:
		context->read_addr = be? vtable_read_addr_be16 : vtable_read_addr_le16;
		break;
	case 4:
		context->read_addr = be? vtable_read_addr_be32 : vtable_read_addr_le32;
		break;
	case 8:
		context->read_addr = be? vtable_read_addr_be64 : vtable_read_addr_le64;
		break;
	default:
		return false;
	}
	return true;
}
