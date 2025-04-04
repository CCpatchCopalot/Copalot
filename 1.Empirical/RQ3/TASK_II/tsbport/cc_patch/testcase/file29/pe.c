/* radare2 - LGPL - Copyright 2021 - condret */

#include <r_io.h>
#include <r_util.h>


R_API RIOBank *r_io_bank_new(const char *name) {
	RIOBank *bank = R_NEW0 (RIOBank);
	if (!bank) {
		return NULL;
	}
	bank->name = strdup (name);
	bank->submaps = r_crbtree_new (free);
	if (!bank->submaps) {
		free (bank);
		return NULL;
	}
	bank->maprefs = r_list_newf (free);
	if (!bank->maprefs) {
		r_crbtree_free (bank->submaps);
		free (bank);
		return NULL;
	}
	bank->todo = r_queue_new (8);
	if (!bank->todo) {
		r_list_free (bank->maprefs);
		r_crbtree_free (bank->submaps);
		free (bank);
		return NULL;
	}
	return bank;
}

R_API void r_io_bank_clear (RIOBank *bank) {
	if (!bank) {
		return;
	}
	while (!r_queue_is_empty (bank->todo)) {
		free (r_queue_dequeue (bank->todo));
	}
	bank->last_used = NULL;
	r_crbtree_clear (bank->submaps);
	r_list_purge (bank->maprefs);
}

R_API void r_io_bank_free(RIOBank *bank) {
	if (!bank) {
		return;
	}
	r_queue_free (bank->todo);
	r_list_free (bank->maprefs);
	r_crbtree_free (bank->submaps);
	free (bank->name);
	free (bank);
}

R_API void r_io_bank_init(RIO *io) {
	r_return_if_fail (io);
	r_io_bank_fini (io);
	io->banks = r_id_storage_new (0, UT32_MAX);
}


static bool _bank_free_cb(void *user, void *data, ut32 id) {
	r_io_bank_free ((RIOBank *)data);
	return true;
}

R_API void r_io_bank_fini(RIO *io) {
	r_return_if_fail (io);
	if (io->banks) {
		r_id_storage_foreach (io->banks, _bank_free_cb, NULL);
		r_id_storage_free (io->banks);
		io->banks = NULL;
	}
}

R_API RIOBank *r_io_bank_get(RIO *io, const ut32 bankid) {
	r_return_val_if_fail (io && io->banks, NULL);
	return (RIOBank *)r_id_storage_get (io->banks, bankid);
}

R_API ut32 r_io_bank_first(RIO *io) {
	ut32 bankid = -1;
	r_id_storage_get_lowest (io->banks, &bankid);
	return bankid;
}

R_API bool r_io_bank_use(RIO *io, ut32 bankid) {
	RIOBank *bank = r_io_bank_get (io, bankid);
	if (bank) {
		io->bank = bankid;
		return true;
	}
	return false;
}

R_API bool r_io_bank_add(RIO *io, RIOBank *bank) {
	r_return_val_if_fail (io && io->banks && bank, false);
	return r_id_storage_add (io->banks, bank, &bank->id);
}

static RIOMapRef *_mapref_from_map(RIOMap *map) {
	RIOMapRef *mapref = R_NEW (RIOMapRef);
	if (!mapref) {
		return NULL;
	}
	mapref->id = map->id;
	mapref->ts = map->ts;
	return mapref;
}

// incoming - in
// cb for finding sm by lower boundary vaddr
static int _find_sm_by_from_vaddr_cb(void *incoming, void *in, void *user) {
	RIOSubMap *bd = (RIOSubMap *)incoming, *sm = (RIOSubMap *)in;
	if (r_io_submap_from (bd) < r_io_submap_from (sm)) {
		return -1;
	}
	if (r_io_submap_from (bd) > r_io_submap_from (sm)) {
		return 1;
	}
	return 0;
}

static int _find_sm_by_vaddr_cb(void *incoming, void *in, void *user) {
	const ut64 addr = ((ut64 *)incoming)[0];
	RIOSubMap *sm = (RIOSubMap *)in;
	if (r_io_submap_contain (sm, addr)) {
		return 0;
	}
	if (addr < r_io_submap_from (sm)) {
		return -1;
	}
	return 1;
}

static int _find_lowest_intersection_sm_cb(void *incoming, void *in, void *user) {
	RIOSubMap *bd = (RIOSubMap *)incoming, *sm = (RIOSubMap *)in;
	if (r_io_submap_overlap (bd, sm)) {
		return 0;
	}
	if (r_io_submap_from (bd) < r_io_submap_from (sm)) {
		return -1;
	}
	return 1;
}

// returns the node containing the submap with lowest itv.addr, that intersects with sm
static RRBNode *_find_entry_submap_node(RIOBank *bank, RIOSubMap *sm) {
	RRBNode *node = r_crbtree_find_node (bank->submaps, sm, _find_lowest_intersection_sm_cb, NULL);
	if (!node) {
		return NULL;
	}
	RRBNode *prev = r_rbnode_prev (node);
	while (prev && r_io_submap_overlap (((RIOSubMap *)prev->data), sm)) {
		node = prev;
		prev = r_rbnode_prev (node);
	}
	return node;
}

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
	ut64 smto = r_io_submap_to (sm);
	if (entry) {
		ut64 ento = r_io_submap_to (((RIOSubMap*)entry->data));
		while (entry && ento <= smto) {
		//delete all submaps that are completly included in sm
		RRBNode *next = r_rbnode_next (entry);
		// this can be optimized, there is no need to do search here
			ento = r_io_submap_to (((RIOSubMap*)entry->data));
			bool a = r_crbtree_delete (bank->submaps, entry->data, _find_sm_by_from_vaddr_cb, NULL);
			if (!a) {
				next = NULL;
			}
		entry = next;
		}
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

R_API bool r_io_bank_map_add_bottom(RIO *io, const ut32 bankid, const ut32 mapid) {
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
		r_list_prepend (bank->maprefs, mapref);
		return true;
	}
	while (entry && r_io_submap_from (((RIOSubMap *)entry->data)) <= r_io_submap_to (sm)) {
		RIOSubMap *bd = (RIOSubMap *)entry->data;
		if (r_io_submap_from (sm) < r_io_submap_from (bd)) {
			RIOSubMap *bdsm = R_NEWCOPY (RIOSubMap, sm);
			r_io_submap_set_to (bdsm, r_io_submap_from (bd) - 1);
			r_crbtree_insert (bank->submaps, bdsm, _find_sm_by_from_vaddr_cb, NULL);
		}
		if (r_io_submap_to (sm) <= r_io_submap_to (bd)) {
			r_list_prepend (bank->maprefs, mapref);
			free (sm);
			return true;
		}
		r_io_submap_set_from (sm, r_io_submap_to (bd) + 1);
		entry = r_rbnode_next (entry);
	}
	r_crbtree_insert (bank->submaps, sm, _find_sm_by_from_vaddr_cb, NULL);
	r_list_prepend (bank->maprefs, mapref);
	return true;
}

R_API bool r_io_bank_map_priorize(RIO *io, const ut32 bankid, const ut32 mapid) {
	RIOBank *bank = r_io_bank_get (io, bankid);
	r_return_val_if_fail (io && bank, false);
	RListIter *iter;
	RIOMapRef *mapref;
	r_list_foreach (bank->maprefs, iter, mapref) {
		if (mapref->id == mapid) {
			goto found;
		}
	}
	return false;
found:
	if (iter == bank->maprefs->tail) {	//tail is top
		return r_io_map_get_by_ref (io, mapref) ? true : false;
	}
	RIOSubMap *sm = r_io_submap_new (io, mapref);
	if (!sm) {
		return false;
	}
	RRBNode *entry = _find_entry_submap_node (bank, sm);
	if (!entry) {
		// if this happens, something is really fucked up
		free (sm);
		return false;
	}
	bank->last_used = NULL;
	RIOSubMap *bd = (RIOSubMap *)entry->data;
	if (r_itv_eq (bd->itv, sm->itv)) {
		// no need to insert new sm, if boundaries match perfectly
		// instead override mapref of existing node/submap
		bd->mapref = *mapref;
		free (sm);
		r_list_iter_to_top (bank->maprefs, iter);
		return true;
	}
	if (r_io_submap_from (bd) < r_io_submap_from (sm) &&
		r_io_submap_to (sm) < r_io_submap_to (bd)) {
		// bd completly overlaps sm on both ends,
		// therefor split bd into 2 maps => bd and bdsm
		// |---bd---||--sm--|-bdsm-|
		RIOSubMap *bdsm = R_NEWCOPY (RIOSubMap, bd);
		if (!bdsm) {
			free (sm);
			return false;
		}
		r_io_submap_set_from (bdsm, r_io_submap_to (sm) + 1);
		r_io_submap_set_to (bd, r_io_submap_from (sm) - 1);
		// TODO: insert and check return value, before adjusting sm size
		r_list_iter_to_top (bank->maprefs, iter);
		return r_crbtree_insert (bank->submaps, sm, _find_sm_by_from_vaddr_cb, NULL) &
			r_crbtree_insert (bank->submaps, bdsm, _find_sm_by_from_vaddr_cb, NULL);
	}

	if (r_io_submap_from (bd) < r_io_submap_from (sm)) {
		r_io_submap_set_to (bd, r_io_submap_from (sm) - 1);
		entry = r_rbnode_next (entry);
	}
	while (entry && r_io_submap_to (((RIOSubMap *)entry->data)) <= r_io_submap_to (sm)) {
		RRBNode *next = r_rbnode_next (entry);
		//delete all submaps that are completly included in sm
		// this can be optimized, there is no need to do search here
		r_crbtree_delete (bank->submaps, entry->data, _find_sm_by_from_vaddr_cb, NULL);
		entry = next;
	}
	if (entry && r_io_submap_from (((RIOSubMap *)entry->data)) <= r_io_submap_to (sm)) {
		bd = (RIOSubMap *)entry->data;
		r_io_submap_set_from (bd, r_io_submap_to (sm) + 1);
	}
	r_list_iter_to_top (bank->maprefs, iter);
	return r_crbtree_insert (bank->submaps, sm, _find_sm_by_from_vaddr_cb, NULL);
}

// deletes submaps that belong to a mapref with a specified priority from the submap tree of a bank.
// the mapref is accessed by it's iter from the priority list in the bank,
// so that the function can insert new submaps that fill the gaps. The iter represents the priority of the mapref.
// this function DOES NOT delete the iter from the list. (that way it can be used for delete and relocate)
static void _delete_submaps_from_bank_tree(RIO *io, RIOBank *bank, RListIter *prio, RIOMap *map) {
	RIOSubMap fake_sm;
	fake_sm.itv = map->itv;
	fake_sm.mapref.id = map->id;
	RRBNode *entry = _find_entry_submap_node (bank, &fake_sm);
	RIOSubMap *bd = (RIOSubMap *)entry->data;
	while (bd && r_io_submap_overlap (bd, (&fake_sm))) {
		// this loop deletes all affected submaps from the rbtree
		// and also enqueues them in bank->todo
		RRBNode *next = r_rbnode_next (entry);
		if (bd->mapref.id == fake_sm.mapref.id) {
			r_queue_enqueue (bank->todo, R_NEWCOPY (RIOSubMap, bd));
			r_crbtree_delete (bank->submaps, bd, _find_sm_by_from_vaddr_cb, NULL);
		}
		entry = next;
		bd = entry ? (RIOSubMap *)entry->data : NULL;
	}
	RListIter *iter = prio;
	while (!r_queue_is_empty (bank->todo)) {
		// now check for each deleted submap if a lower map intersects with it
		// and create new submaps accordingly, and fill the gaps
		RIOSubMap *sm = r_queue_dequeue (bank->todo);
		RListIter *ator = r_list_iter_get_prev (iter);
		while (ator) {
			map = r_io_map_get_by_ref (io, (RIOMapRef *)ator->data);
			ator = r_list_iter_get_prev (ator);
			if (!map) {
				// if this happens, something is fucked up, and no submap should be inserted
				continue;
			}
			// if the map and sm intersect, the intersecting submap needs to be inserted in the tree
			// there are 5 cases to consider here
			// 1. no intersection: just continue to the next iteration
			// 2. map overlaps sm on both ends: insert submap for map with boundaries of sm
			// 3. map overlaps sm on the upper end: insert submap for map accordingly and adjust sm boundaries
			// 4. map overlaps sm on the lower end: insert submap for map accordingly and adjust sm boundaries
			// 5. sm overlaps sm on both ends: split sm into 2 submaps and enqueue new one in banks->todo; insert submap for map; adjust sm boundaries
			if (r_io_submap_to (sm) < r_io_map_from (map) || r_io_submap_from (sm) > r_io_map_to (map)) {
				// case 1
				continue;
			}
			RIOMapRef *mapref = _mapref_from_map (map);
			bd = r_io_submap_new (io, mapref);
			free (mapref);
			if (!bd) {
				continue;
			}
			if (r_io_submap_from (sm) >= r_io_map_from (map)) {
				// case 4 and 2
				r_io_submap_set_from (bd, r_io_submap_from (sm));
				r_crbtree_insert (bank->submaps, bd, _find_sm_by_from_vaddr_cb, NULL);
				if (r_io_submap_to (sm) <= r_io_map_to (map)) {
					// case 2
					r_io_submap_set_to (bd, r_io_submap_to (sm));
					break;
				}
				// case 4
				r_io_submap_set_from (sm, r_io_submap_to (bd) + 1);
				continue;
			}
			if (r_io_submap_to (sm) <= r_io_map_to (map)) {
				// case 3
				// adjust bd upper boundary to avoid overlap with existing submaps
				r_io_submap_set_to (bd, r_io_submap_to (sm));
				// adjust sm upper boundary to avoid hitting again on sm in further iterations
				r_io_submap_set_to (sm, r_io_submap_from (bd) - 1);
				r_crbtree_insert (bank->submaps, bd, _find_sm_by_from_vaddr_cb, NULL);
				continue;
			}
			// case 5 because all other cases are already handled
			RIOSubMap *bdsm = R_NEWCOPY (RIOSubMap, sm);
			r_io_submap_set_to (sm, r_io_submap_from (bd) - 1);
			r_io_submap_set_from (bdsm, r_io_submap_to (bd) + 1);
			r_crbtree_insert (bank->submaps, bd, _find_sm_by_from_vaddr_cb, NULL);
			r_queue_enqueue (bank->todo, bdsm);
		}
		free (sm);
	}
}

R_API bool r_io_bank_map_depriorize(RIO *io, const ut32 bankid, const ut32 mapid) {
	RIOBank *bank = r_io_bank_get (io, bankid);
	RIOMap *map = r_io_map_get (io, mapid);
	r_return_val_if_fail (bank && map, false);
	RListIter *iter;
	RIOMapRef *mapref = NULL;
	r_list_foreach (bank->maprefs, iter, mapref) {
		if (mapref->id == mapid) {
			goto found;
		}
	}
	// map is not referenced by this bank
	return false;
found:
	if (iter == bank->maprefs->head) {
		// map is already lowest priority
		return true;
	}
	bank->last_used = NULL;
	_delete_submaps_from_bank_tree (io, bank, iter, map);
	r_list_delete (bank->maprefs, iter);
	return r_io_bank_map_add_bottom (io, bankid, mapid);
}

// compared 2 maprefs of the same bank by their priority (position in  the mapref list)
// returns 0, if both have the same priority
// returns 1, if mr0 has higher priority than mr1
// returns -1, if mr1 has higher priority tham mr0
// returns 0, if neither mr0 nor mr1 are an element of the bank
static int _mapref_priority_cmp(RIOBank *bank, RIOMapRef *mr0, RIOMapRef *mr1) {
	if (mr0->id == mr1->id) {
		// mapref have the same priority, if their mapid matches
		return 0;
	}
	RListIter *iter;
	RIOMapRef *mapref;
	r_list_foreach_prev (bank->maprefs, iter, mapref) {
		if (mapref->id == mr0->id) {
			return 1;
		}
		if (mapref->id == mr1->id) {
			return -1;
		}
	}
	return 0;	// should never happen
}

R_API bool r_io_bank_update_map_boundaries(RIO *io, const ut32 bankid, const ut32 mapid, ut64 ofrom, ut64 oto) {
	RIOBank *bank = r_io_bank_get (io, bankid);
	r_return_val_if_fail (io && bank, false);
	RListIter *iter;
	RIOMapRef *mapref;
	r_list_foreach_prev (bank->maprefs, iter, mapref) {
		if (mapref->id == mapid) {
			goto found;
		}
	}
	// map is not referenced by this map
	return false;
found:
	;RIOMap *map = r_io_map_get_by_ref (io, mapref);
	if (!map) {
		// inconsistent mapref
		// mapref should be deleted from bank here
		return false;
	}
	if (r_io_map_from (map) == ofrom && r_io_map_to (map) == oto) {
		// nothing todo here
		return true;
	}
	// allocate sm here to avoid deleting things without ensuring
	// that this code could at least insert 1 submap
	RIOSubMap *sm = r_io_submap_new (io, mapref);
	if (!sm) {
		return false;
	}

	bank->last_used = NULL;
	// this problem can be divided in 2 steps:
	// 1. delete corresponding submaps and insert intersecting submaps with lower priority
	// 2. adjust addr and insert submaps at new addr respecting priority
	RIOMap fake_map;
	memcpy (&fake_map, map, sizeof (RIOMap));
	fake_map.itv.addr = ofrom;
	fake_map.itv.size = oto - ofrom + 1;
	_delete_submaps_from_bank_tree (io, bank, iter, &fake_map);

	RRBNode *entry = _find_entry_submap_node (bank, sm);
	if (!entry) {
		// no intersection here, so just insert sm into the tree and we're done
		r_crbtree_insert (bank->submaps, sm, _find_sm_by_from_vaddr_cb, NULL);
		// assumption here is that there is no need to check for return value of r_crbtree_insert,
		// since it only fails, if allocation fails and a delete was performed before, so it should just be fine
		return true;
	}

	RIOSubMap *bd = (RIOSubMap *)entry->data;
	// check if sm has higher priority than bd by comparing their maprefs
	if (_mapref_priority_cmp (bank, &sm->mapref, &bd->mapref) == 1) {
		// sm has higher priority that bd => adjust bd
		if (r_io_submap_to (bd) == r_io_submap_to (sm)) {
			if (r_io_submap_from (bd) >= r_io_submap_from (sm)) {
				// bc of _find_entry_submap_node, we can be sure, that there is no
				// lower submap that intersects with sm
				//
				// instead of deleting and inserting, just replace the mapref,
				// similar to r_io_bank_map_priorize
				memcpy (bd, sm, sizeof (RIOSubMap));
				free (sm);
			} else {
				r_io_submap_set_to (bd, r_io_submap_from (sm) - 1);
				r_crbtree_insert (bank->submaps, sm, _find_sm_by_from_vaddr_cb, NULL);
			}
			return true;
		}
		if (r_io_submap_from (bd) < r_io_submap_from (sm) &&
			r_io_submap_to (sm) < r_io_submap_to (bd)) {
			RIOSubMap *bdsm = R_NEWCOPY (RIOSubMap, bd);
			// allocating bdsm here is fine, bc bd is already in the tree
			r_io_submap_set_from (bdsm, r_io_submap_to (sm) + 1);
			r_io_submap_set_to (bd, r_io_submap_from (sm) - 1);
			// What do if this fails?
			r_crbtree_insert (bank->submaps, sm, _find_sm_by_from_vaddr_cb, NULL);
			r_crbtree_insert (bank->submaps, bdsm, _find_sm_by_from_vaddr_cb, NULL);
			return true;
		}
		if (r_io_submap_from (bd) < r_io_submap_from (sm)) {
			r_io_submap_set_to (bd, r_io_submap_from (sm) - 1);
			entry = r_rbnode_next (entry);
		}
	} else {
		// _mapref_priority_cmp cannot return 0 in this scenario,
		// since all submaps with the same mapref as sm were deleted from
		// the submap tree previously. so _mapref_priority_cmp can only return 1 or -1
		// bd has higher priority than sm => adjust sm
		if (r_io_submap_from (bd) <= r_io_submap_from (sm)) {
			if (r_io_submap_to (sm) <= r_io_submap_to (bd)) {
				// bd completly overlaps sm => nothing to do
				free (sm);
				return true;
			} // else
			// adjust sm
			// r_io_submap_set_from (sm, r_io_submap_to (bd) + 1);
		} else {
			if (r_io_submap_to (sm) <= r_io_submap_to (bd)) {
				r_io_submap_set_to (sm, r_io_submap_from (bd) - 1);
				if (!r_crbtree_insert (bank->submaps, sm, _find_sm_by_from_vaddr_cb, NULL)) {
					free (sm);
					return false;
				}
				return true;
			}
			RIOSubMap *bdsm = R_NEWCOPY (RIOSubMap, sm);
			if (!bdsm) {
				free (sm);
				return false;
			}
			r_io_submap_set_to (bdsm, r_io_submap_from (bd) - 1);
			// r_io_submap_set_from (sm, r_io_submap_to (bd) + 1);
			if (!r_crbtree_insert (bank->submaps, bdsm, _find_sm_by_from_vaddr_cb, NULL)) {
				free (bdsm);
				free (sm);
				return false;
			}
			// r_io_submap_set_from (sm, r_io_submap_to (bd) + 1);
			entry = r_rbnode_next (entry);
		}
		r_io_submap_set_from (sm, r_io_submap_to (bd) + 1);
	}
	// entry = r_rbnode_next (entry);
	// it is given that entry->data->from >= sm->from on every iteration
	// so only check for upper boundary of sm for intersection with entry->data
	while (entry && r_io_submap_to (((RIOSubMap *)entry->data)) <= r_io_submap_to (sm)) {
		// iterate forwards starting at entry, while entry->data and sm overlap
		bd = (RIOSubMap *)entry->data;
		entry = r_rbnode_next (entry);
		// check if sm has higher priority than bd by comparing their maprefs
		if (_mapref_priority_cmp (bank, &sm->mapref, &bd->mapref) == 1) {
			// delete bd
			r_crbtree_delete (bank->submaps, bd, _find_sm_by_from_vaddr_cb, NULL);
		} else {
			// _mapref_priority_cmp cannot return 0 in this scenario,
			// since all submaps with the same mapref as sm were deleted from
			// the submap tree previously. so _mapref_priority_cmp can only return 1 or -1
			// bd has higher priority than sm => adjust sm
			if (r_io_submap_from (bd) > r_io_submap_from (sm)) {
				RIOSubMap *bdsm = R_NEWCOPY (RIOSubMap, sm);
				r_io_submap_set_to (bdsm, r_io_submap_from (bd) - 1);
				r_crbtree_insert (bank->submaps, bdsm, _find_sm_by_from_vaddr_cb, NULL);
			}
			if (r_io_submap_to (bd) == r_io_submap_to (sm)) {
				// in this case the size of sm would be 0,
				// but since empty maps are not allowed free sm and return
				free (sm);
				return true;
			}
			r_io_submap_set_from (sm, r_io_submap_to (bd) + 1);
		}
	}
	if (!entry) {
		return r_crbtree_insert (bank->submaps, sm, _find_sm_by_from_vaddr_cb, NULL);
	}
	bd = (RIOSubMap *)entry->data;
	if (_mapref_priority_cmp (bank, &sm->mapref, &bd->mapref) == 1) {
		if (r_io_submap_from (bd) <= r_io_submap_to (sm)) {
			r_io_submap_set_from (bd, r_io_submap_to (sm) + 1);
		}
		r_crbtree_insert (bank->submaps, sm, _find_sm_by_from_vaddr_cb, NULL);
	} else {
		if (r_io_submap_from (sm) < r_io_submap_from (bd)) {
			if (r_io_submap_from (bd) <= r_io_submap_to (sm)) {
				r_io_submap_set_to (sm, r_io_submap_from (bd) - 1);
			}
			r_crbtree_insert (bank->submaps, sm, _find_sm_by_from_vaddr_cb, NULL);
		} else {
			// can this happen?
			free (sm);
		}
	}
	return true;
}

// locates next available address for a map with given size and alignment starting at *addr
R_API bool r_io_bank_locate(RIO *io, const ut32 bankid, ut64 *addr, const ut64 size, ut64 load_align) {
	RIOBank *bank = r_io_bank_get (io, bankid);
	r_return_val_if_fail (io && bank && bank->submaps && addr && size, false);
	if (load_align == 0LL) {
		load_align = 1;
	}
	RIOSubMap fake_sm;
	memset (&fake_sm, 0x00, sizeof(RIOSubMap));
	fake_sm.itv.addr = *addr + (load_align - *addr % load_align) % load_align;
	fake_sm.itv.size = size;
	RRBNode *entry = _find_entry_submap_node (bank, &fake_sm);
	if (!entry) {
		// no submaps in this bank
		*addr = fake_sm.itv.addr;
		return true;
	}
	// this is a bit meh: first iteration can never be successful,
	// bc entry->sm will always intersect with fake_sm, if
	// _find_entry_submap_node suceeded previously
	ut64 next_location = fake_sm.itv.addr;
	while (entry) {
		RIOSubMap *sm = (RIOSubMap *)entry->data;
		if (size <= r_io_submap_from (sm) - next_location) {
			*addr = next_location;
			return true;
		}
		next_location = (r_io_submap_to (sm) + 1) +
			(load_align - ((r_io_submap_to (sm) + 1) % load_align)) % load_align;
		entry = r_rbnode_next (entry);
	}
	if (next_location == 0LL) {
		// overflow from last submap in the tree => no location
		return false;
	}
	if (UT64_MAX - size + 1 < next_location) {
		return false;
	}
	*addr = next_location;
	return true;
}

R_API bool r_io_bank_read_at(RIO *io, const ut32 bankid, ut64 addr, ut8 *buf, int len) {
	RIOBank *bank = r_io_bank_get (io, bankid);
	r_return_val_if_fail (io && bank, false);
	RIOSubMap fake_sm;
	memset (&fake_sm, 0x00, sizeof(RIOSubMap));
	fake_sm.itv.addr = addr;
	fake_sm.itv.size = len;
	RRBNode *node;
	if (bank->last_used && r_io_submap_contain (((RIOSubMap *)bank->last_used->data), addr)) {
		node = bank->last_used;
	} else {
		node = _find_entry_submap_node (bank, &fake_sm);
	}
	memset (buf, io->Oxff, len);
	RIOSubMap *sm = node ? (RIOSubMap *)node->data : NULL;
	bool ret = true;
	while (sm && r_io_submap_overlap ((&fake_sm), sm)) {
		bank->last_used = node;
		RIOMap *map = r_io_map_get_by_ref (io, &sm->mapref);
		if (!map) {
			// mapref doesn't belong to map
			return false;
		}
		if (!(map->perm & R_PERM_R)) {
			node = r_rbnode_next (node);
			sm = node ? (RIOSubMap *)node->data : NULL;
			continue;
		}
		const ut64 buf_off = R_MAX (addr, r_io_submap_from (sm)) - addr;
		const int read_len = R_MIN (r_io_submap_to ((&fake_sm)),
					     r_io_submap_to (sm)) - (addr + buf_off) + 1;
		const ut64 paddr = addr + buf_off - r_io_map_from (map) + map->delta;
		ret &= (r_io_fd_read_at (io, map->fd, paddr, &buf[buf_off], read_len) == read_len);
		// check return value here?
		node = r_rbnode_next (node);
		sm = node ? (RIOSubMap *)node->data : NULL;
	}
	return ret;
}

R_API bool r_io_bank_write_at(RIO *io, const ut32 bankid, ut64 addr, const ut8 *buf, int len) {
	RIOBank *bank = r_io_bank_get (io, bankid);
	r_return_val_if_fail (io && bank, false);
	RIOSubMap fake_sm;
	memset (&fake_sm, 0x00, sizeof(RIOSubMap));
	fake_sm.itv.addr = addr;
	fake_sm.itv.size = len;
	RRBNode *node;
	if (bank->last_used && r_io_submap_contain (((RIOSubMap *)bank->last_used->data), addr)) {
		node = bank->last_used;
	} else {
		node = _find_entry_submap_node (bank, &fake_sm);
	}
	RIOSubMap *sm = node ? (RIOSubMap *)node->data : NULL;
	bool ret = true;
	while (sm && r_io_submap_overlap ((&fake_sm), sm)) {
		bank->last_used = node;
		RIOMap *map = r_io_map_get_by_ref (io, &sm->mapref);
		if (!map) {
			// mapref doesn't belong to map
			return false;
		}
		if (!(map->perm & R_PERM_W)) {
			node = r_rbnode_next (node);
			sm = node ? (RIOSubMap *)node->data : NULL;
			continue;
		}
		const ut64 buf_off = R_MAX (addr, r_io_submap_from (sm)) - addr;
		const int write_len = R_MIN (r_io_submap_to ((&fake_sm)),
					     r_io_submap_to (sm)) - (addr + buf_off) + 1;
		const ut64 paddr = addr + buf_off - r_io_map_from (map) + map->delta;
		ret &= (r_io_fd_write_at (io, map->fd, paddr, &buf[buf_off], write_len) == write_len);
		// check return value here?
		node = r_rbnode_next (node);
		sm = node ? (RIOSubMap *)node->data : NULL;
	}
	return ret;
}

// reads only from single submap at addr and returns amount of bytes read.
// if no submap is mapped at addr, fcn returns 0. returns -1 on error
R_API int r_io_bank_read_from_submap_at(RIO *io, const ut32 bankid, ut64 addr, ut8 *buf, int len) {
	RIOBank *bank = r_io_bank_get (io, bankid);
	r_return_val_if_fail (io && bank, -1);
	if (!len) {
		return 0;
	}
	RRBNode *node;
	if (bank->last_used && r_io_submap_contain (((RIOSubMap *)bank->last_used->data), addr)) {
		node = bank->last_used;
	} else {
		node = r_crbtree_find_node (bank->submaps, &addr, _find_sm_by_vaddr_cb, NULL);
		if (!node) {
			return 0;
		}
		bank->last_used = node;
	}
	RIOSubMap *sm = (RIOSubMap *)node->data;
	if (!r_io_submap_contain (sm, addr)) {
		return 0;
	}
	RIOMap *map = r_io_map_get_by_ref (io, &sm->mapref);
	if (!map || !(map->perm & R_PERM_R)) {
		return -1;
	}
	const int read_len = R_MIN (len, r_io_submap_to (sm) - addr + 1);
	const ut64 paddr = addr - r_io_map_from (map) + map->delta;
	return r_io_fd_read_at (io, map->fd, paddr, buf, read_len);
}

// writes only to single submap at addr and returns amount of bytes written.
// if no submap is mapped at addr, fcn returns 0. returns -1 on error
R_API int r_io_bank_write_to_submap_at(RIO *io, const ut32 bankid, ut64 addr, const ut8 *buf, int len) {
	RIOBank *bank = r_io_bank_get (io, bankid);
	r_return_val_if_fail (io && bank, -1);
	if (!len) {
		return 0;
	}
	RRBNode *node;
	if (bank->last_used && r_io_submap_contain (((RIOSubMap *)bank->last_used->data), addr)) {
		node = bank->last_used;
	} else {
		node = r_crbtree_find_node (bank->submaps, &addr, _find_sm_by_vaddr_cb, NULL);
		if (!node) {
			return 0;
		}
		bank->last_used = node;
	}
	RIOSubMap *sm = (RIOSubMap *)node->data;
	if (!r_io_submap_contain (sm, addr)) {
		return 0;
	}
	RIOMap *map = r_io_map_get_by_ref (io, &sm->mapref);
	if (!map || !(map->perm & R_PERM_W)) {
		return -1;
	}
	const int write_len = R_MIN (len, r_io_submap_to (sm) - addr + 1);
	const ut64 paddr = addr - r_io_map_from (map) + map->delta;
	return r_io_fd_write_at (io, map->fd, paddr, buf, write_len);
}

R_API RIOMap *r_io_bank_get_map_at(RIO *io, const ut32 bankid, ut64 addr) {
	RIOBank *bank = r_io_bank_get (io, bankid);
	r_return_val_if_fail (io && bank, NULL);
	RRBNode *node = r_crbtree_find_node (bank->submaps, &addr, _find_sm_by_vaddr_cb, NULL);
	if (!node) {
		return NULL;
	}
	RIOSubMap *sm = (RIOSubMap *)node->data;
	if (!r_io_submap_contain (sm, addr)) {
		return NULL;
	}
	return r_io_map_get_by_ref (io, &sm->mapref);
}

// deletes map with mapid from bank with bankid
R_API void r_io_bank_del_map(RIO *io, const ut32 bankid, const ut32 mapid) {
	// no need to check for mapref here, since this is "just" deleting
	RIOBank *bank = r_io_bank_get (io, bankid);
	RIOMap *map = r_io_map_get (io, mapid);	//is this needed?
	r_return_if_fail (bank && map);
	RListIter *iter;
	RIOMapRef *mapref = NULL;
	r_list_foreach_prev (bank->maprefs, iter, mapref) {
		if (mapref->id == map->id) {
			_delete_submaps_from_bank_tree (io, bank, iter, map);
			r_list_delete (bank->maprefs, iter);
			break;
		}
	}
	// map is not referenced by this bank; nothing to do
}

R_API void r_io_bank_del(RIO *io, const ut32 bankid) {
	r_id_storage_delete (io->banks, bankid);
	if (io->bank == bankid) {
		io->bank = r_io_bank_first (io);
	}
}

// merges nearby submaps, that have a map ref to the same map, and free unneeded tree nodes
R_API void r_io_bank_drain(RIO *io, const ut32 bankid) {
	r_return_if_fail (io);
	RIOBank *bank = r_io_bank_get (io, bankid);
	if (!bank) {
		return;
	}
	bank->last_used = NULL;
	RRBNode *node = r_crbtree_first_node (bank->submaps);
	RRBNode *next = NULL;
	while (node) {
		next = r_rbnode_next (node);
		if (next) {
			RIOSubMap *bd = (RIOSubMap *)node->data;
			RIOSubMap *sm = (RIOSubMap *)next->data;
			if (!memcmp (&bd->mapref, &sm->mapref, sizeof (RIOMapRef))) {
				r_io_submap_set_to (bd, r_io_submap_to (sm));
				r_crbtree_delete (bank->submaps, sm, _find_sm_by_from_vaddr_cb, NULL);
				continue;
			}
		}
		node = next;
	}
}

bool io_bank_has_map(RIO *io, const ut32 bankid, const ut32 mapid) {
	RIOBank *bank = r_io_bank_get (io, bankid);
	r_return_val_if_fail (io && bank, false);
	RListIter *iter;
	RIOMapRef *mapref;
	r_list_foreach (bank->maprefs, iter, mapref) {
		if (mapref->id == mapid) {
			return true;
		}
	}
	return false;
}
