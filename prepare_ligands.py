#!/usr/bin/env python

##########################################################################
# Author: joemartaganna (joemar.ct@gmail.com)
#
# Description:
#
# Script for converting mol2 files downloaded from the ZINC database into 
# pdbqt files with charges and polar hydrogens added in preparation for 
# docking with AutoDock Vina. The conversion is done in parallel through
# multithreading.
#
# Requires: babel, joblib
##########################################################################


from subprocess import Popen, PIPE
from joblib import Parallel, delayed
import gzip
import os

    
def convert_to_pdbqt(mol2, output_dir, remove_input=True):
    mol_id = mol2.split('\n')[1]
    # Write the mol2
    mol2_outf_path = os.path.join(output_dir, mol_id + '.mol2')
    mol2_outf = open(mol2_outf_path, 'w')
    mol2_outf.write(mol2)
    mol2_outf.close()
    # Convert to pdbqt
    pdbqt_outf_path = mol2_outf_path.replace('.mol2', '.pdbqt')
    cmd = 'babel -imol2 %s -opdbqt %s --partialcharge gasteiger --AddPolarH' % (mol2_outf_path, pdbqt_outf_path)
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    if remove_input:
        os.remove(mol2_outf_path)
    return {'mol2': mol2_outf_path, 'pdbqt': pdbqt_outf_path}
            

def split_gzipped_mol2(gzipped_mol2, output_dir=None):
    f = gzip.open(gzipped_mol2, 'rb').read()
    p = '@<TRIPOS>MOLECULE'
    mols_count = f.count(p)
    mols = f.split(p)
    if not output_dir:
        output_dir = gzipped_mol2.split('.mol2.gz')[0]
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
    def format_mol(mol):
        mol = [p] + [x.strip() for x in mol.split('\n') if x]
        mol = '\n'.join(mol)
        return mol
    mols = [format_mol(x) for x in mols if x]
    return mols
    

def generate_pdbqt_files(gzipped_mol2, mols):
    output_dir = gzipped_mol2.split('.mol2.gz')[0]
    Parallel(n_jobs=50, backend='threading', verbose=55)(delayed(convert_to_pdbqt)(mol, output_dir) for mol in mols)
    

if __name__ == '__main__':
    import sys
    infiles = sys.argv[1:]
    for i, f in enumerate(infiles):
        print '\n\n%s/%s - dealing with %s' % (i+1, len(infiles), f)
        mols = split_gzipped_mol2(f)
        generate_pdbqt_files(f, mols)