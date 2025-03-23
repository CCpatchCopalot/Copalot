static pyc_object *get_set_object(RBuffer *buffer) {
	bool error = false;
	ut32 n = get_ut32 (buffer, &error);
	if (n > ST32_MAX) {
		eprintf ("bad marshal data (set size out of range)\n");
		return NULL;
	}
	if (error) {
		return NULL;
	}
	pyc_object *ret = get_array_object_generic (buffer, n);
	if (ret) {
		ret->type = TYPE_SET;
	}
	return ret;
}
