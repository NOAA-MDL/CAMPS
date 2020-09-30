****************************************************************************************************************************************************************
Appendix A:  Proposed enhancements to `Guidelines for Construction of CF Standard Names <http://cfconventions.org/Data/cf-standard-names/docs/guidelines.html>`_
****************************************************************************************************************************************************************

The Guidelines (hereafter, [GCSN]) enumerate two transformations directly associated with probabilities--they specify a probability_distribution_of_X[_over Z] and a probability_density_function_of_X[_over Z].
We propose the following additional transformation:


+----------------------------------+---------+----------------------------------------+
| Rule                             |  Units  |               Meaning                  |
+==================================+=========+========================================+
| event_probability_of_X[_over_Z]  |    1    | probability of occurrence for a        |
|                                  |         | defined event associated with X.  The  |
|                                  |         | data variable should have an axis for  |
|                                  |         | X and Z or declare them as auxiliary   |
|                                  |         | variables.                             |
+----------------------------------+---------+----------------------------------------+
| parameterized_probability        |         | conveys the characteristics of the     |
| _distribution_of_X[_over_Z]      |    1    | weather element.  Ancillary variables  |
|                                  |         | convey the distribution parameter      |
|                                  |         | values.                                |
+----------------------------------+---------+----------------------------------------+

Of course, additional information is required to enable proper interpretation of the probabilities.
The details of that additional information need not be specified in [GCSN].
