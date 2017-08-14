

def main():
    lines = readFile()  # An array of lines

    for l in lines:
        read_variable(l)


def readVariable(var_str):
    source = get_source(var_str)  # str
    observed_property = get_observed_property(var_str)  # str
    is_predictor = get_is_predictor(var_str)  # bool
    lead_time = get_lead_time(var_str)
