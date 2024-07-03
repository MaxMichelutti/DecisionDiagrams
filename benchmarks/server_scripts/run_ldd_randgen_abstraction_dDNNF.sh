#!/bin/bash

mkdir ./benchmarks/ldd_randgen/output_dDNNF_abstract
mkdir ./benchmarks/ldd_randgen/tmp_abstract


for gen in ./benchmarks/ldd_randgen/data/*
do
	outputgen="${gen/data/output_dDNNF_abstract}"
	tmpgen="${gen/data/tmp_abstract}"
	mkdir $outputgen
	mkdir $tmpgen
	for probs in $gen/*
	do
		outputprobs="${probs/data/output_dDNNF_abstract}"
		tmpprobs="${probs/data/tmp_abstract}"
		mkdir $outputprobs
		mkdir $tmpprobs
		for item in $probs/*
		do
			smtfilename="${item#"$probs"/}"
			jsonfilename="${smtfilename/.smt2/.json}"
			tmpfile="${item/data/tmp_abstract}"
			tmpjsonfile="${tmpfile/.smt2/.json}"
			tmpfolder="${tmpfile/.smt2/_c2d}"
			#echo $smtfilename
			#echo $jsonfilename
			#echo $tmpfile
			if [ -f "$outputprobs"/"$jsonfilename" ]; then
				echo "Skipping task on $smtfilename"
			else
				echo "Performing task on $smtfilename"
				python main.py -i "$item" --load_lemmas "$tmpfile" --abstraction_dDNNF -d "$outputprobs"/"$jsonfilename" --no_dDNNF_to_pysmt --keep_c2d_temp "$tmpfolder"
				echo "Task completed on $smtfilename"
			fi
		done
	done
done
