static pyc_object *get_array_object_generic(RBuffer *buffer, ut32 size) {
	pyc_object *tmp = NULL;
	pyc_object *ret = NULL;
	ut32 i = 0;

	ret = R_NEW0 (pyc_object);
	if (!ret) {
		return NULL;
	}
	ret->data = r_list_newf ((RListFree)free_object);
	if (!ret->data) {
		free (ret);
		return NULL;
	}
	for (i = 0; i < size; i++) {
		tmp = get_object (buffer);
		if (!tmp) {
			r_list_free (ret->data);
			R_FREE (ret);
			return NULL;
		}
		if (!r_list_append (ret->data, tmp)) {
			free_object (tmp);
			r_list_free (ret->data);
			free (ret);
			return NULL;
		}
	}
	return ret;
}
