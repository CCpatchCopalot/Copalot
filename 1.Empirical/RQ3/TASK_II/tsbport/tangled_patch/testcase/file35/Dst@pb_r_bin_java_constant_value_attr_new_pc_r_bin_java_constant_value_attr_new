R_API RBinJavaAttrInfo *r_bin_java_constant_value_attr_new(RBinJavaObj *bin, ut8 *buffer, ut64 sz, ut64 buf_offset) {
	ut64 offset = 6;
	RBinJavaAttrInfo *attr = r_bin_java_default_attr_new (bin, buffer, sz, buf_offset);
	if (attr) {
		attr->type = R_BIN_JAVA_ATTR_TYPE_CONST_VALUE_ATTR;
		attr->info.constant_value_attr.constantvalue_idx = R_BIN_JAVA_USHORT (buffer, offset);
		offset += 2;
		attr->size = offset;
	}
	// IFDBG r_bin_java_print_constant_value_attr_summary(attr);
	return attr;
}
