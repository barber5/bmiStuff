python pheno/cfier.py diabcc.txt 1500 .2 diab.ignore diab/fimp_diab_part_nocids.txt -dt 10320 61045 2977 meds codes labs > diab/out_diab_part_nocids.txt
python pheno/cfier.py diabcc.txt 1500 .2 diab.ignore diab/fimp_diab_part_cids.txt -dt 10320 61045 2977 meds codes labs cids > diab/out_diab_part_cids.txt
python pheno/cfier.py diabcc.txt 1500 .2 diab.ignore diab/fimp_diab_part_terms.txt -dt 10320 61045 2977 meds codes labs terms > diab/out_diab_part_terms.txt
python pheno/cfier.py diabcc.txt 1500 .2 diab.ignore diab/fimp_diab_part_cidsterms.txt -dt 10320 61045 2977 meds codes labs cids terms > diab/out_diab_part_cidsterms.txt
python pheno/cfier.py diabcc.txt 1500 .2 diab.ignore diab/fimp_diab_full_nocids.txt meds codes labs > diab/out_diab_full_nocids.txt
python pheno/cfier.py diabcc.txt 1500 .2 diab.ignore diab/fimp_diab_full_cids.txt meds codes labs cids > diab/out_diab_full_cids.txt
python pheno/cfier.py diabcc.txt 1500 .2 diab.ignore diab/fimp_diab_full_terms.txt meds codes labs terms > diab/out_diab_full_terms.txt
python pheno/cfier.py diabcc.txt 1500 .2 diab.ignore diab/fimp_diab_full_cidsterms.txt meds codes labs cids terms > diab/out_diab_full_cidsterms.txt
