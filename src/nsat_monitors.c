/* ************************************************************************
 * NSATlib_v2 This is a C implementation of the NSATlib_v2 python
 * script. It simulates the NSAT. 
 * Copyright (C) <2016>  UCI, Georgios Detorakis (gdetor@protonmail.com)
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 **************************************************************************/
#include "nsat.h"


/* ************************************************************************
 * OPEN_MONITOR_FILE: This function opens a file and returns the file 
 * pointer. 
 *
 * Args : 
 *  fname (char *)    : File name (to open)
 *  buff (char *)     : A characters buffer containing the number of 
 *                      each epoch in string format
 *  ext (char *)      : The extension .dat of the output files    
 *
 * Returns :
 *  File pointer fp otherwise it terminates with an error signal.
 **************************************************************************/
FILE *open_monitor_file(char *fname) {
    FILE *fp = NULL;
    fp = fopen(fname, "wb");
    file_test(fp, fname);
    return fp;
}


/* ************************************************************************
 * OPEN_CORES_MONITOR_FILES: This function opens monitor files and returns
 * the corresponding file pointers. 
 *
 * Args : 
 *  core (nsat_core *)   : Cores structs vector
 *  fnames (char *)      : File names (to open)
 *  num_cores (size_t)   : Number of cores
 *
 * Returns :
 *  File pointer fp otherwise it terminates with an error signal.
 **************************************************************************/
void open_cores_monitor_files(nsat_core *core, fnames *fname, size_t num_cores) {
    size_t p;
    char *filename = NULL;

    for(p = 0; p < num_cores; ++p) {
        /* Initialize state monitors */
        if (core[p].mon_pms->mon_states) {
            filename = gen_fname(fname->states, p, 1);
            core[p].files->fs = open_monitor_file(filename);
            dealloc(filename);
        }

        /* Intialize state monitors for FPGA */
        if (core[p].mon_pms->mon_states_fpga) {
            filename = gen_fname(fname->states, p, 0);
            core[p].files->fsa = open_monitor_file(filename);
            dealloc(filename);
        }

        /* Initialize weights monitors */
        if (core[p].mon_pms->mon_weights) {
            filename = gen_fname(fname->synw, p, 1);
            core[p].files->fw = open_monitor_file(filename);
            dealloc(filename);
        }
#if DAVIS == 1
    open_online_spike_monitor(&core, fname);
#endif

    }
}


/* ************************************************************************
 * CLOSE_CORES_MONITOR_FILES: This function closes monitor files and returns
 * the corresponding file pointers. 
 *
 * Args : 
 *  core (nsat_core *)   : Cores structs vector
 *  num_cores (size_t)   : Number of cores
 *
 * Returns :
 *  File pointer fp otherwise it terminates with an error signal.
 **************************************************************************/
void close_cores_monitor_files(nsat_core *core, size_t num_cores) {
    size_t p;

    for (p = 0; p < num_cores; ++p) {
        /* Close all monitor files */
        if (core[p].mon_pms->mon_states) {
            fclose(core[p].files->fs);
        }
        if (core[p].mon_pms->mon_states_fpga) {
            fclose(core[p].files->fsa);
        }
        if (core[p].mon_pms->mon_weights) {
            fclose(core[p].files->fw);
        }
    }
}


/* ************************************************************************
 * UPDATE_STATE_MONITOR_FILE: This functions writes at every predefined
 * time checkpoint all neurons states into a binary file. 
 *
 * Args : 
 *  core (nsat_core *)    : Core struct pointer
 *
 * Returns :
 *  void
 **************************************************************************/
void update_state_monitor_file(nsat_core *core) {
    unsigned long long j;
    unsigned int k;

    fwrite(&core->curr_time, sizeof(int), 1, core->files->fs);
    for(j = 0; j < core->core_pms.num_neurons; ++j) {
        for(k = 0; k < core->core_pms.num_states; ++k) {
            fwrite(&core->nsat_neuron[j].s[k].x,
                   sizeof(STATETYPE),
                   1,
                   core->files->fs);
        }
    }
}


/* ************************************************************************
 * UPDATE_STATE_MONITOR_FILE: This functions writes at every predefined
 * time checkpoint all neurons states into a binary file. 
 *
 * Args : 
 *  core (nsat_core *)    : Core struct pointer
 *
 * Returns :
 *  void
 **************************************************************************/
void update_state_monitor_online(nsat_core *core) {
    unsigned long long j;
    unsigned int k;

    fwrite(&core->curr_time, sizeof(int), 1, core->files->fs);
    for(j = 0; j < core->core_pms.num_neurons; ++j) {
        if (core->nsat_neuron[j].is_spk_rec_on) {
            for(k = 0; k < core->core_pms.num_states; ++k) {
                fwrite(&core->nsat_neuron[j].s[k].x,
                       sizeof(STATETYPE),
                       1,
                       core->files->fs);
            }
        }
    }
}


/* ************************************************************************
 * STORE_FPGA_STATES: This functions writes at every predefined
 * time checkpoint all neurons states into a ascii file in hex format.
 * Output files from this function are used with FPGAs.
 *
 * Args : 
 *  core (nsat_core *)  : Core struct pointer
 *
 * Returns :
 *  void
 **************************************************************************/
void store_fpga_states(nsat_core *core) {
    unsigned long long j;
    unsigned int k;
    
    for(j = 0; j < core->core_pms.num_neurons; ++j) {
        for(k = 0; k < core->core_pms.num_states; ++k) {
            fprintf(core->files->fsa, "%08llx  ", core->curr_time);
            fprintf(core->files->fsa, "%08llx  ", j);
            fprintf(core->files->fsa, "%08x  ", k);
            fprintf(core->files->fsa, "%08x\n", core->nsat_neuron[j].s[k].x);
        }
    }
}


/* ************************************************************************
 * UPDATE_MONITOR_NEXT_STATE: This function writes the current time step 
 * NSAT neurons activity for each state. 
 *
 * Args : 
 *  x (int *)           : State 
 *  fp  (FILE * )       : Pointer to the output file
 *  num_neurons (int)   : Number of neurons
 *  num_states (int)    : Number of states
 *
 * Returns :
 *  void
 **************************************************************************/
void update_monitor_next_state(int *x,
                               FILE *fp,
                               int num_neurons,
                               int num_states) {
    int j, k;

    for(j = 0; j < num_neurons; ++j) {
        for(k = 0; k < num_states; ++k) {
            fwrite(&x[j*num_states+k], sizeof(int), 1, fp);
        }
    }
}


/* ************************************************************************
 * UPDATE_SYNAPTIC_STRENGTH_MONITOR_FILE: This functions writes at every
 * predefined time checkpoint all neurons synaptic strengths in binary 
 * file. 
 *
 * Args : 
 *  core (nsat_core *)  : Core struct pointer
 *
 * Returns :
 *  void
 **************************************************************************/
void update_synaptic_strength_monitor_file(nsat_core *core) {
    unsigned int k;
    unsigned long long tmp, tmp2;
    unsigned long long i, num_inputs = core->core_pms.num_inputs;
    unsigned long long num_neurons = core->core_pms.num_neurons;
    unsigned int num_states = core->core_pms.num_states;
    syn_list_node *ptr = NULL;
    id_list_node *ptr_id = NULL;

    /* Write external neurons weights */
    for (k = 0; k < num_states; ++k) {
        for(i = 0; i< num_inputs; ++i) {    /* all pre neurons */
            ptr = core->ext_neuron[i].syn_ptr[k]->head;  /* pre neuron */
            while (ptr != NULL) {   /*  loop over post of pre neuron */
                ptr_id = core->core_pms.ext_syn_rec_ids->head; /* init targets */
                while (ptr_id != NULL) {  /* loop over targets */
                    /* Time */
                    tmp = ptr_id->id; 
                    if (tmp == ptr->id){   /* if target == post of pre neuron then write */
                        fwrite(&core->curr_time, sizeof(unsigned long long), 1, core->files->fw);
                        /* Source */
                        fwrite(&i, sizeof(unsigned long long), 1, core->files->fw);
                        /* Destination */
                        tmp = tmp + num_inputs;
                        fwrite(&tmp, sizeof(unsigned long long), 1, core->files->fw);
                        /* State */
                        fwrite(&k, sizeof(unsigned int), 1, core->files->fw);
                        /* Weight value */
                        /* ptr->W is the weight from pre to post */
                        fwrite(ptr->w_ptr, sizeof(WTYPE), 1, core->files->fw);
                    }
                    ptr_id = ptr_id->next;
                }
                ptr = ptr->next;
            }
        }
    }

    for (k = 0; k < num_states; ++k) {
        for(i = 0; i < num_neurons; ++i) {   /* all pre neurons */
            ptr = core->nsat_neuron[i].syn_ptr[k]->head;  /* pre neuron  */
            while (ptr != NULL) {   /* loop over post of pre neuron  */
                ptr_id = core->core_pms.nsat_syn_rec_ids->head;   /* init targets  */
                while (ptr_id != NULL) {  /* loop over targets */
                    /* Time */
                    tmp = ptr_id->id; 
                    if (tmp == ptr->id){  /* if target == post of pre neuron then write */
                        fwrite(&core->curr_time, sizeof(unsigned long long), 1, core->files->fw);
                        /* Source */
                        tmp2 = i + num_inputs;
                        fwrite(&tmp2, sizeof(unsigned long long), 1, core->files->fw);
                        /* Destination */
                        tmp = tmp + num_inputs;
                        fwrite(&tmp, sizeof(unsigned long long), 1, core->files->fw);
                        /* State */
                        fwrite(&k, sizeof(unsigned int), 1, core->files->fw);
                        /* Weight value */
                        /* ptr->W is the weight from pre to post */
                        fwrite(ptr->w_ptr, sizeof(WTYPE), 1, core->files->fw); 
                    }
                    ptr_id = ptr_id->next;
                }
                ptr = ptr->next;
            }
        }
    }
}


void open_online_spike_monitor(nsat_core **cores, fnames *fname){
    unsigned int p;
    char *filename=NULL;                     /* Tmp filename */  

    for (p = 0; p < (*cores)[0].g_pms->num_cores; ++p) {
        filename = gen_fname(fname->events, p, 1);
        if(!((*cores)[p].files->event_file = fopen(filename, "wb"))) {
            printf("File %s cannot be opened!\n", filename);
            exit(-1);
        }
        dealloc(filename);
    }
}
