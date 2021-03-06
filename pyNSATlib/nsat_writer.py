#!/bin/python
# ----------------------------------------------------------------------------
# File Name :
# Author: Emre Neftci
#
# Creation Date : Wed 01 Feb 2017 10:56:20 AM PST
# Last Modified : Fri Feb 10 08:56:07 PST 2017
#
# Copyright : (c) UC Regents, Emre Neftci
# Licence : GPLv2
# -----------------------------------------------------------------------------
import numpy as np
import warnings
import os
from .utils import *
from .global_vars import *
from ctypes import Structure, c_char_p
from pyNCSre import pyST


def pack(data, typ='i'):
    import struct
    data = np.array(data).flatten()
    s = struct.pack(typ * data.shape[0], *data.astype(typ))
    return s


class DataStruct(object):
    pass


class NSATWriter(object):

    def __init__(self, config_nsat, path, prefix='sim'):
        self.cfg = config_nsat
        if not os.path.exists(path):
            warnings.warn('Path {0} does not exist, creating'.format(path))
            os.makedirs(path)
        self.fname = self.generate_c_fnames(path + '/' + prefix)

    def write(self, write_events=True,
              write_weights=True,
              write_corecfgs=True):
        '''
        Writes all parameter files for running c_nsat software simulation.
        inputs:
        *path*: string defining which path the files should be stored into
        *write_events*: Boolean defining whether synaptic should be written or
                        not.
                        Useful when synaptic weights are imported from another
                        experiment
        *write_events*: Boolean defining whether external events should be
                        generated or not.
                        Useful when external events generation is long or
                        imported from another experiment
        '''
        if not self.cfg.groups_set:
            self.cfg.set_groups()

        if write_corecfgs:
            self.write_corecfgs()

        if self.cfg.ext_evts:
            self.write_ext_events()

        if write_weights:
            self.write_L0connectivity()
            self.write_L1connectivity()


class c_nsat_fnames(Structure):
    """ fnames class implements the C struct: fnames. Contains the
        filenames of all the necessary input files.
    """
    _fields_ = [('nsat_params_map', c_char_p),
                ('lrn_params_map', c_char_p),
                ('params', c_char_p),
                ('syn_wgt_table', c_char_p),
                ('syn_ptr_table', c_char_p),
                ('ext_events', c_char_p),
                ('synw', c_char_p),
                ('synw_final', c_char_p),
                ('events', c_char_p),
                ('states', c_char_p),
                ('check_pms', c_char_p),
                ('stdp_fun', c_char_p),
                ('stats_nsat', c_char_p),
                ('stats_ext', c_char_p),
                ('l1_conn', c_char_p),
                ('shared_mem', c_char_p)]


class C_NSATWriter(NSATWriter):
    # Struct contains all the file names

    def generate_c_fnames(self, path):
        fname = c_nsat_fnames()
        fname.nsat_params_map = (path + "_nsat_params_map.dat").encode('utf-8')
        fname.lrn_params_map = (path + "_lrn_params_map.dat").encode('utf-8')
        fname.params = (path + "_params.dat").encode('utf-8')
        fname.syn_wgt_table = (path + "_wgt_table").encode('utf-8')
        fname.syn_ptr_table = (path + "_ptr_table").encode('utf-8')
        fname.ext_events = (path + "_ext_events").encode('utf-8')
        fname.synw = (path + "_weights").encode('utf-8')
        fname.synw_final = (path + "_weights_final").encode('utf-8')
        fname.events = (path + "_events").encode('utf-8')
        fname.states = (path + "_states").encode('utf-8')
        fname.check_pms = (path + "_cpms.dat").encode('utf-8')
        fname.stdp_fun = (path + "_stdp_fun.dat").encode('utf-8')
        fname.stats_nsat = (path + "_stats_nsat").encode('utf-8')
        fname.stats_ext = (path + "_stats_ext").encode('utf-8')
        fname.l1_conn = (path + "_l1_conn.dat").encode('utf-8')
        fname.shared_mem = (path + "_shared_mem").encode('utf-8')
        return fname

    def write_globals(self):
        # Globals are written in write_corecfgs
        pass

    def write_corecfgs(self):
        '''
        Write all parameters for c_nsat simulations
        *inputs*: fnames
        *outputs*: None
        '''
        cfg = self.cfg
        with open(self.fname.params, 'wb') as fh:
            # Global parameters
            fh.write(pack(cfg.N_CORES, 'I'))
            fh.write(pack(cfg.single_core, '?'))
            if len(cfg.L1_connectivity) != 0:
                cfg.routing_en = True
            fh.write(pack(cfg.routing_en, '?'))
            fh.write(pack(cfg.sim_ticks, 'Q'))
            fh.write(pack(cfg.seed, 'Q'))
            fh.write(pack(cfg.s_seq, 'Q'))
            fh.write(pack(cfg.is_bm_rng_on, '?'))
            fh.write(pack(cfg.is_clock_on, '?'))
            fh.write(pack(cfg.w_check, '?'))
            fh.write(pack(cfg.w_boundary, 'i'))

            # Core parameters
            for p, core_cfg in cfg:
                fh.write(pack(cfg.ext_evts, '?'))
                fh.write(pack(cfg.plasticity_en[p], '?'))
                fh.write(pack(cfg.gated_learning[p], '?'))
                fh.write(pack(core_cfg.n_inputs, 'Q'))
                fh.write(pack(core_cfg.n_neurons, 'Q'))
                fh.write(pack(core_cfg.n_states, 'I'))
                fh.write(pack(core_cfg.n_groups, 'I'))
                fh.write(pack(core_cfg.n_lrngroups, 'I'))
                fh.write(pack(cfg.rec_deltat, 'Q'))
                fh.write(pack(cfg.num_syn_ids_rec[p], 'Q'))
                fh.write(pack(cfg.syn_ids_rec[p], 'Q'))

            # NSAT parameters
            for p, core_cfg in cfg:
                for j in range(core_cfg.n_groups):
                    fh.write(pack(core_cfg.gate_lower[j], 'i'))
                    fh.write(pack(core_cfg.gate_upper[j], 'i'))
                    fh.write(pack(core_cfg.learn_period[j], 'I'))
                    fh.write(pack(core_cfg.learn_burnin[j], 'I'))
                    fh.write(pack(core_cfg.t_ref[j], 'i'))
                    fh.write(pack(core_cfg.modstate[j], 'i'))
                    fh.write(pack(core_cfg.prob_syn[j], 'i'))
                    fh.write(pack(core_cfg.A[j].T, 'i'))
                    fh.write(pack(core_cfg.sA[j].T, 'i'))
                    fh.write(pack(core_cfg.b[j], 'i'))
                    fh.write(pack(core_cfg.Xreset[j], 'i'))
                    fh.write(pack(core_cfg.Xthlo[j], 'i'))
                    fh.write(pack(core_cfg.XresetOn[j], '?'))
                    fh.write(pack(core_cfg.Xthup[j], 'i'))
                    fh.write(pack(core_cfg.XspikeIncrVal[j], 'i'))
                    fh.write(pack(core_cfg.sigma[j], 'i'))
                    fh.write(pack(core_cfg.flagXth[j], '?'))
                    fh.write(pack(core_cfg.Xth[j], 'i'))
                    fh.write(pack(core_cfg.Wgain[j], 'i'))

                fh.write(pack(core_cfg.Xinit.flatten(), 'i'))
                fh.write(pack(np.shape(cfg.spk_rec_mon[p])[0], 'Q'))
                fh.write(pack(cfg.spk_rec_mon[p], 'Q'))

            # Learning parameters
            for p, core_cfg in cfg:
                if cfg.plasticity_en[p]:
                    fh.write(pack(cfg.tstdpmax[p], 'i'))
                    for j in range(core_cfg.n_lrngroups):
                        fh.write(pack(core_cfg.tstdp[j], 'i'))
                        fh.write(pack(core_cfg.plastic[j], '?'))
                        fh.write(pack(core_cfg.stdp_en[j], '?'))
                        fh.write(pack(core_cfg.is_stdp_exp_on[j], '?'))
                        fh.write(pack(core_cfg.tca[j], 'i'))
                        fh.write(pack(core_cfg.hica[j], 'i'))
                        fh.write(pack(core_cfg.sica[j], 'i'))
                        fh.write(pack(core_cfg.slca[j], 'i'))
                        fh.write(pack(core_cfg.tac[j], 'i'))
                        fh.write(pack(core_cfg.hiac[j], 'i'))
                        fh.write(pack(core_cfg.siac[j], 'i'))
                        fh.write(pack(core_cfg.slac[j], 'i'))
                        fh.write(pack(core_cfg.is_rr_on[j], '?'))
                        fh.write(pack(core_cfg.rr_num_bits[j], 'i'))

            # Monitor parameters
            # TODO: Separately for every core
            for p, core_cfg in cfg:
                fh.write(pack(cfg.monitor_states, '?'))
                fh.write(pack(cfg.monitor_states, '?'))
                fh.write(pack(cfg.monitor_weights, '?'))
                fh.write(pack(cfg.monitor_weights_final, '?'))
                fh.write(pack(cfg.monitor_spikes, '?'))
                fh.write(pack(cfg.monitor_stats, '?'))

            """ Thee following generates the mapping function.
                Fow now this is a vector with numbers in [0, 8),
                and every element corresponds to a NSAT neuron
                unit.
                Example:
                    If the user would like to have three (3)
                    different parameters groups for 30 neurons
                    then they have to do the following:
                    nmap = np.zeros((num_neurons, dtype='i'))
                    nmap[10:20] = 1
                    nmap[20:30] = 2
                    Of course one can mix the parameters and
                    neurons but it's not recommended.
            """

            # nmap = np.zeros((num_neurons, ), dtype='i')
        with open(self.fname.nsat_params_map, 'wb') as f:
            for p, core_cfg in cfg:
                f.write(pack(core_cfg.nmap, 'i'))

        # nmap = np.zeros((num_neurons, ), dtype='i')
        with open(self.fname.lrn_params_map, 'wb') as f:
            for p, core_cfg in cfg:
                lrnmap_unrolled = np.zeros(
                    [core_cfg.n_neurons, core_cfg.n_states], dtype='int')
                for i in range(core_cfg.n_neurons):
                    lrnmap_unrolled[i, :] = core_cfg.lrnmap[
                        core_cfg.nmap[i], :]
                lrnmap_unrolled = lrnmap_unrolled.flatten()
                f.write(pack(lrnmap_unrolled, 'i'))

    def _find_first(self, a, i):
        for j, v in enumerate(a):
            if v == i:
                return j

    def write_ext_events(self):
        if self.cfg.ext_evts_data == True:
            return
        from collections import Counter
        cfg = self.cfg
        events = cfg.ext_evts_data
        for core in list(events.keys()):
            events[core].sort_tm()
            ad, tm = events[core].get_adtm()
            tm_count = Counter(tm)
            tms = list(range(1, cfg.sim_ticks))
            pos_t = 0
            filename = self.fname.ext_events + \
                ('_core_' + str(core) + '.dat').encode('utf-8')
            with open(filename, 'wb') as fe:
                for t in tms:
                    tc = tm_count[t]
                    fe.write(pack([t, tc], 'Q'))
                    if tc > 0:
                        delta_pos = self._find_first(tm[pos_t:], t)
                        data = ad[(pos_t + delta_pos):(pos_t + delta_pos + tc)]
                        pos_t = pos_t + delta_pos + tc
                        fe.write(pack(data, 'Q'))

    def write_L0connectivity(self):
        self.write_L0_ptr_table()
        self.write_L0_wgt_table()

    def write_L0_ptr_table(self):
        for p, core_cfg in self.cfg:
            from scipy.sparse import issparse
            filename = self.fname.syn_ptr_table + \
                ('_core_' + str(p) + '.dat').encode('utf-8')
            with open(filename, 'wb') as fw:
                if issparse(core_cfg.ptr_table):
                    cw = core_cfg.ptr_table.tocoo()
                    nonzero_elems = cw.nnz
                    src_nrn = cw.row.astype('uint64').astype('uint64')
                    dst_nrn = (cw.col % core_cfg.n_units).astype('uint64')
                    dst_state = (cw.col // core_cfg.n_units).astype('uint64')
                    ptr_data = np.column_stack(
                        [src_nrn, dst_nrn, dst_state, cw.data])
                    fw.write(pack(nonzero_elems, 'Q'))
                    fw.write(pack(ptr_data, 'Q'))
                else:  # Non sparse compatibility
                    cw = core_cfg.ptr_table
                    nonzero_elems = np.count_nonzero(cw)
                    c0 = np.argwhere(np.array(cw) != 0)
                    c1 = cw[np.array(cw) != 0]
                    c = np.column_stack([c0, c1])
                    fw.write(pack(c, 'Q'))

    def write_L0_wgt_table(self):
        for p, core_cfg in self.cfg:
            filename = self.fname.syn_wgt_table + \
                ('_core_' + str(p) + '.dat').encode('utf-8')
            with open(filename, 'wb') as fw:
                fw.write(pack(core_cfg.wgt_table, 'i'))

    def write_L1connectivity(self):
        L1 = self.cfg.L1_connectivity
        with open(self.fname.l1_conn, 'wb') as fw:
            fw.write(pack(len(L1), 'i'))
            for src, dsts in L1.items():
                nonzero_elems = 0
                if(isinstance(dsts[0], tuple)):
                    nonzero_elems = len((dsts))
                else:
                    nonzero_elems = len(np.shape(dsts))
                nonzero_elems = len((dsts))
                fw.write(pack(src[0], 'I'))
                fw.write(pack(src[1], 'Q'))
                fw.write(pack(nonzero_elems, 'Q'))
                for dst in dsts:
                    x, y = dst
                    fw.write(pack(dst[0], 'I'))
                    fw.write(pack(dst[1], 'Q'))


def check_network_sizes(core_cfg):
    cond1 = core_cfg.n_states * core_cfg.n_neurons <= N_TOT
    str1 = "Maximum number of neurons is {0}".format(N_TOT / core_cfg.n_states)
    cond2 = len(core_cfg.ntypes) <= N_TOT * 2
    str2 = "Maximum number of neurons and axons is {0}".format(N_TOT * 2)
    return [cond1, str1], [cond2, str2]


def compute_syn_en_mask(ptr_table):
    '''
    For global parameter that indicates which states across a core recieve
    inputs.
    '''
    mask = 0
    for i in range(ptr_table.shape[2]):
        mask += np.any(ptr_table[:, :, i] != 0) * 2**i
    return mask


class C_NSATWriterSingleThread(C_NSATWriter):

    def write_ext_events(self):
        if self.cfg.ext_evts_data is True:
            return
        from collections import Counter
        cfg = self.cfg
        events = cfg.ext_evts_data
        ad, tm = events.flatten().get_adtm()
        tm_count = Counter(tm)
        tms = list(range(1, cfg.sim_ticks))
        pos_t = 0
        filename = self.fname.ext_events
        with open(filename, 'wb') as fe:
            for t in tms:
                tc = tm_count[t]
                fe.write(pack([t, tc], 'Q'))
                if tc > 0:
                    delta_pos = self._find_first(tm[pos_t:], t)
                    data = ad[(pos_t + delta_pos):(pos_t + delta_pos + tc)]
                    pos_t = pos_t + delta_pos + tc
                    data = list(
                        zip(data >> CHANNEL_OFFSET, data & (ADDR_MASK)))
                    fe.write(pack(data, 'Q'))


def read_from_file(fname):
    import struct as st
    with open(fname, "rb") as f:
        cont = f.read()
    size = int(len(cont) / 4)
    return np.array(st.unpack('i' * size, cont))


if __name__ == '__main__':
    from .NSATlib import ConfigurationNSAT, exportAER, build_SpikeList
    cfg = ConfigurationNSAT(N_CORES=2,
                            N_INPUTS=[10, 10],
                            N_NEURONS=[512, 100],
                            N_STATES=[4, 2],
                            bm_rng=True,
                            ben_clock=True)

    cfg.core_cfgs[0].W[:cfg.core_cfgs[0].n_inputs,
                       cfg.core_cfgs[0].n_inputs:] = 1
    cfg.core_cfgs[0].CW[:cfg.core_cfgs[0].n_inputs,
                        cfg.core_cfgs[0].n_inputs:] = 1
    cfg.core_cfgs[1].W[:cfg.core_cfgs[1].n_inputs,
                       cfg.core_cfgs[1].n_inputs:] = 1
    cfg.core_cfgs[1].CW[:cfg.core_cfgs[1].n_inputs,
                        cfg.core_cfgs[1].n_inputs:] = 1
    cfg.set_L1_connectivity({(0, 1): ((1, 0), (1, 1))})

    SL1 = build_SpikeList(evs_time=[1, 2, 3], evs_addr=[5, 6, 7])
    SL2 = build_SpikeList(evs_time=[2, 5, 1], evs_addr=[3, 9, 5])
    evs = exportAER([SL1, SL2])
    cfg.set_ext_events(evs)

    c_nsat_writer = C_NSATWriter(cfg, path='/tmp/', prefix='test')
    c_nsat_writer.write()
