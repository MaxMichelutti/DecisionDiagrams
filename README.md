# Knowledge Compilation Tool

## Running

This is the implementation of the code for my project course with professor R. Sebastiani of the University of Trento and doctorands G. Spallitta and G. Masina. 
To try out the code just type in the project folder:

```
    python3 knowledge_compiler.py
```

## Installation

First install the dd package with cython and wheel. This is a fork of the official dd package that can be installed directly from pip, which adds bindings for generating LDDs. You can find more info at [this link](https://github.com/masinag/dd).

```
    pip install --upgrade wheel cython
    export DD_FETCH=1 DD_CUDD=1 DD_LDD=1
    pip install git+https://github.com/masinag/dd.git@main -vvv --use-pep517 --no-build-isolation
```

To check that this step completed successfully, the following command should not yield any errors

```
    python -c 'from dd import ldd; ldd.LDD(ldd.TVPI,0,0)'
```

Then install all other dependencies of the project

```
    pip install -r requirements.txt
```

Finally install the Mathsat SMT-solver from the pysmt package

```
    pysmt-install --msat
```

## Compiling to dDNNF

The tool supports both abstraction based and theory consistent compilation in dDNNF. However, in order to compile to this language you will need to download the dDNNF compiler [c2d](http://reasoning.cs.ucla.edu/c2d/) or the [d4](https://github.com/crillab/d4) dDNNF compiler. Download and compile the binaries and update your .env to point to the correct paths. Remember to grant the compilers permission to execute.

Compilation in dDNNF is currently not supported by the tool for OSs other than Linux.

# Query Tool

To use the query tool on T-d-DNNFs, remmeber to update your ```.env``` file.

You can find the implementation for d-DNNF condition at [this link](https://github.com/MaxMichelutti/dDNNF-Query).

You can find the implementation for Dec d-DNNF [here](https://github.com/crillab/decdnnf_rs).