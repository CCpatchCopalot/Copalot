static pyc_object *get_list_object(RBuffer *buffer) {
	pyc_object *ret = NULL;
	bool error = false;
	ut32 n = 0;

	n = get_ut32 (buffer, &error);
	if (n > ST32_MAX) {
		eprintf ("bad marshal data (list size out of range)\n");
		return NULL;
	}
	if (error) {
		return NULL;
	}
	ret = get_array_object_generic (buffer, n);
	if (ret) {
		ret->type = TYPE_LIST;
		return ret;
	}
	return NULL;
}
