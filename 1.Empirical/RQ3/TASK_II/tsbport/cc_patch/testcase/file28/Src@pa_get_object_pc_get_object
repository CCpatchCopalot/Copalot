static pyc_object *get_object(RBuffer *buffer) {
	bool error = false;
	pyc_object *ret = NULL;
	ut8 code = get_ut8 (buffer, &error);
	ut8 flag = code & FLAG_REF;
	RListIter *ref_idx = NULL;
	ut8 type = code & ~FLAG_REF;

	if (error) {
		return NULL;
	}

	if (flag) {
		ret = get_none_object ();
		if (!ret) {
			return NULL;
		}
		ref_idx = r_list_append (refs, ret);
		if (!ref_idx) {
			free_object (ret);
			return NULL;
		}
	}

	switch (type) {
	case TYPE_NULL:
		free_object (ret);
		return NULL;
	case TYPE_TRUE:
		free_object (ret);
		return get_true_object ();
	case TYPE_FALSE:
		free_object (ret);
		return get_false_object ();
	case TYPE_NONE:
		free_object (ret);
		return get_none_object ();
	case TYPE_REF:
		free_object (ret);
		return get_ref_object (buffer);
	case TYPE_SMALL_TUPLE:
		ret = get_small_tuple_object (buffer);
		break;
	case TYPE_TUPLE:
		ret = get_tuple_object (buffer);
		break;
	case TYPE_STRING:
		ret = get_string_object (buffer);
		break;
	case TYPE_CODE_v0:
		ret = get_code_object (buffer);
		if (ret) {
			ret->type = TYPE_CODE_v0;
		}
		break;
	case TYPE_CODE_v1:
		ret = get_code_object (buffer);
		if (ret) {
			ret->type = TYPE_CODE_v1;
		}
		break;
	case TYPE_INT:
		ret = get_int_object (buffer);
		break;
	case TYPE_ASCII_INTERNED:
		ret = get_ascii_interned_object (buffer);
		break;
	case TYPE_SHORT_ASCII:
		ret = get_short_ascii_object (buffer);
		break;
	case TYPE_ASCII:
		ret = get_ascii_object (buffer);
		break;
	case TYPE_SHORT_ASCII_INTERNED:
		ret = get_short_ascii_interned_object (buffer);
		break;
	case TYPE_INT64:
		ret = get_int64_object (buffer);
		break;
	case TYPE_INTERNED:
		ret = get_interned_object (buffer);
		break;
	case TYPE_STRINGREF:
		ret = get_stringref_object (buffer);
		break;
	case TYPE_FLOAT:
		ret = get_float_object (buffer);
		break;
	case TYPE_BINARY_FLOAT:
		ret = get_binary_float_object (buffer);
		break;
	case TYPE_COMPLEX:
		ret = get_complex_object (buffer); // behaviour depends on Python version
		break;
	case TYPE_BINARY_COMPLEX:
		ret = get_binary_complex_object (buffer);
		break;
	case TYPE_LIST:
		ret = get_list_object (buffer);
		break;
	case TYPE_LONG:
		ret = get_long_object (buffer);
		break;
	case TYPE_UNICODE:
		ret = get_unicode_object (buffer);
		break;
	case TYPE_DICT:
		ret = get_dict_object (buffer);
		break;
	case TYPE_FROZENSET:
	case TYPE_SET:
		ret = get_set_object (buffer);
		break;
	case TYPE_STOPITER:
	case TYPE_ELLIPSIS:
		ret = R_NEW0 (pyc_object);
		break;
	case TYPE_UNKNOWN:
		eprintf ("Get not implemented for type 0x%x\n", type);
		free_object (ret);
		return NULL;
	case 0:
		// nop
		break;
	default:
		eprintf ("Undefined type in get_object (0x%x)\n", type);
		free_object (ret);
		return NULL;
	}

	if (flag && ref_idx) {
		free_object (ref_idx->data);
		ref_idx->data = copy_object (ret);
	}
	return ret;
}
