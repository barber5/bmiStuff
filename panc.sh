python pheno/cfier.py panccc.txt 1500 .2 panc.ignore panc/fimp_panc_part_nocids.txt -dt 10320 61045 2977 meds codes labs > panc/out_panc_part_nocids.txt
python pheno/cfier.py panccc.txt 1500 .2 panc.ignore panc/fimp_panc_part_cids.txt -dt 10320 61045 2977 meds codes labs cids > panc/out_panc_part_cids.txt
python pheno/cfier.py panccc.txt 1500 .2 panc.ignore panc/fimp_panc_part_terms.txt -dt 10320 61045 2977 meds codes labs terms > panc/out_panc_part_terms.txt
python pheno/cfier.py panccc.txt 1500 .2 panc.ignore panc/fimp_panc_part_cidsterms.txt -dt 10320 61045 2977 meds codes labs cids terms > panc/out_panc_part_cidsterms.txt
python pheno/cfier.py panccc.txt 1500 .2 panc.ignore panc/fimp_panc_full_nocids.txt meds codes labs > panc/out_panc_full_nocids.txt
python pheno/cfier.py panccc.txt 1500 .2 panc.ignore panc/fimp_panc_full_cids.txt meds codes labs cids > panc/out_panc_full_cids.txt
python pheno/cfier.py panccc.txt 1500 .2 panc.ignore panc/fimp_panc_full_terms.txt meds codes labs terms > panc/out_panc_full_terms.txt
python pheno/cfier.py panccc.txt 1500 .2 panc.ignore panc/fimp_panc_full_cidsterms.txt meds codes labs cids terms > panc/out_panc_full_cidsterms.txt
