..

  ***************************************
  Appendix B:  Proposed CF standard names
  ***************************************

  +------------------------------------+-----------------------------------+------+------+
  | Standard Name                      | Canonical Units                   | AMIP | GRIB |
  +====================================+================+==================+======+======+
  | probability_distribution_parameter | 1                                 |      |      |
  +------------------------------------+-----------------------------------+------+------+
  | **Description**                    | The value of the named parameter of a           |
  |                                    | probability distribution.  The variable will    |
  |                                    | normally be an Ancillary variable of the        |
  |                                    | distribution variable.  The attribute           |
  |                                    | parameter_name names parameter, and the         |
  |                                    | attribute parameter_reference refers to an      |
  |                                    | authoritative reference for the parameter.      |
  +------------------------------------+-----------------------------------+------+------+
  | present_weather_binary_mask        | 1                                 |      |      |
  +------------------------------------+-----------------------------------+------+------+
  | **Description**                    | X_binary_mask has 1 where condition X is met, 0 |
  |                                    | elsewhere.  1 = the specified present weather   |
  |                                    | is observed or forecast, 0 = not.  The          |
  |                                    | attribute present_weather_list describes the    |
  |                                    | present weather cases that cause 1 or refers    |
  |                                    | to that description.                            |
  +------------------------------------+-------------------------------------------------+
