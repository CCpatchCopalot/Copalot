R_API bool r_io_bank_map_add_top(RIO *io, const ut32 bankid, const ut32 mapid) {
	RIOBank *bank = r_io_bank_get (io, bankid);
	RIOMap *map = r_io_map_get (io, mapid);
	r_return_val_if_fail (io && bank && map, false);
	RIOMapRef *mapref = _mapref_from_map (map);
	if (!mapref) {
		return false;
	}
	RIOSubMap *sm = r_io_submap_new (io, mapref);
	if (!sm) {
		free (mapref);
		return false;
	}
	RRBNode *entry = _find_entry_submap_node (bank, sm);
	if (!entry) {
		// no intersection with any submap, so just insert
		if (!r_crbtree_insert (bank->submaps, sm, _find_sm_by_from_vaddr_cb, NULL)) {
			free (sm);
			free (mapref);
			return false;
		}
		r_list_append (bank->maprefs, mapref);
		return true;
	}
	bank->last_used = NULL;
	RIOSubMap *bd = (RIOSubMap *)entry->data;
	if (r_io_submap_to (bd) == r_io_submap_to (sm) &&
		r_io_submap_from (bd) >= r_io_submap_from (sm)) {
		// _find_entry_submap_node guarantees, that there is no submap
		// prior to bd in the range of sm, so instead of deleting and inserting
		// we can just memcpy
		memcpy (bd, sm, sizeof (RIOSubMap));
		free (sm);
		r_list_append (bank->maprefs, mapref);
		return true;
	}
	if (r_io_submap_from (bd) < r_io_submap_from (sm) &&
		r_io_submap_to (sm) < r_io_submap_to (bd)) {
		// split bd into 2 maps => bd and bdsm
		RIOSubMap *bdsm = R_NEWCOPY (RIOSubMap, bd);
		if (!bdsm) {
			free (sm);
			free (mapref);
			return false;
		}
		r_io_submap_set_from (bdsm, r_io_submap_to (sm) + 1);
		r_io_submap_set_to (bd, r_io_submap_from (sm) - 1);
		// TODO: insert and check return value, before adjusting sm size
		if (!r_crbtree_insert (bank->submaps, sm, _find_sm_by_from_vaddr_cb, NULL)) {
			free (sm);
			free (bdsm);
			free (mapref);
			return false;
		}
		if (!r_crbtree_insert (bank->submaps, bdsm, _find_sm_by_from_vaddr_cb, NULL)) {
			r_crbtree_delete (bank->submaps, sm, _find_sm_by_from_vaddr_cb, NULL);
			free (sm);
			free (bdsm);
			free (mapref);
			return false;
		}
		r_list_append (bank->maprefs, mapref);
		return true;
	}

	// guaranteed intersection
	if (r_io_submap_from (bd) < r_io_submap_from (sm)) {
		r_io_submap_set_to (bd, r_io_submap_from (sm) - 1);
		entry = r_rbnode_next (entry);
	}
	while (entry && r_io_submap_to (((RIOSubMap *)entry->data)) <= r_io_submap_to (sm)) {
		//delete all submaps that are completly included in sm
		RRBNode *next = r_rbnode_next (entry);
		// this can be optimized, there is no need to do search here
		r_crbtree_delete (bank->submaps, entry->data, _find_sm_by_from_vaddr_cb, NULL);
		entry = next;
	}
	if (entry && r_io_submap_from (((RIOSubMap *)entry->data)) <= r_io_submap_to (sm)) {
		bd = (RIOSubMap *)entry->data;
		r_io_submap_set_from (bd, r_io_submap_to (sm) + 1);
	}
	if (!r_crbtree_insert (bank->submaps, sm, _find_sm_by_from_vaddr_cb, NULL)) {
		free (sm);
		free (mapref);
		return false;
	}
	r_list_append (bank->maprefs, mapref);
	return true;
}
