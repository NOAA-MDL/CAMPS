
Wisps Data Object
=================

General
-------
The Wisps Data class should be a representation of ANY kind of 'WISPS'
formatted data. That is, the data can be gridded or vector, it can
may or may not have a lead time associated with it, and can be 
n-dimensional.


Dimensions
----------
Allowing for the flexiblility of the object, the number of dimensions of the
data are unlimited. However, these dimensions should be able to be 
identified. 

For example, 
Assume there is a variable that is gridded and is a snapshot of a single time. 
This variable would have three dimensions: x, y, and time. 
Another variable is a vector of stations and includes lead time at 
various times. This would also have three dimensions, number of stations,
lead time, and time.

These separate variables should be distinguished based on other metadata.




