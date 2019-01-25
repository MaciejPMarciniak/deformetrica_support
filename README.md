# deformetrica_support
Helper functions for building files used by deformetrica
In deformetrica files (model.xml, data-set.xml, optimization-parameters.xml) many of the fields depend on the files
    used to build the model. This superclass finds all the relevant files (i.e. the file names) and puts them in
    a format easy to parse with xml tree. It also asserts that if a model is split into elements, all elements
    of a given model exist.
