python pheno/cfier.py pancreatitis.txt 1400 .2 panc.ignore fimp_panc_part_nocids.txt -dt 10320 61045 2977 meds codes labs > out_panc_part_nocids.txt
python pheno/cfier.py pancreatitis.txt 1400 .2 panc.ignore fimp_panc_part_cids.txt -dt 10320 61045 2977 meds codes labs cids > out_panc_part_cids.txt
python pheno/cfier.py pancreatitis.txt 1400 .2 panc.ignore fimp_panc_part_terms.txt -dt 10320 61045 2977 meds codes labs terms > out_panc_part_terms.txt
python pheno/cfier.py pancreatitis.txt 1400 .2 panc.ignore fimp_panc_part_cidsterms.txt -dt 10320 61045 2977 meds codes labs cids terms > out_panc_part_cidsterms.txt
python pheno/cfier.py pancreatitis.txt 1400 .2 panc.ignore fimp_panc_full_nocids.txt meds codes labs > out_panc_full_nocids.txt
python pheno/cfier.py pancreatitis.txt 1400 .2 panc.ignore fimp_panc_full_cids.txt meds codes labs cids > out_panc_full_cids.txt
python pheno/cfier.py pancreatitis.txt 1400 .2 panc.ignore fimp_panc_full_terms.txt meds codes labs terms > out_panc_full_terms.txt
python pheno/cfier.py pancreatitis.txt 1400 .2 panc.ignore fimp_panc_full_cidsterms.txt meds codes labs cids terms > out_panc_full_cidsterms.txt
