import logging
from collections import Counter

all_qc_errors = []


class qc_error:

    def __init__(self, station_name="UNKN", station_type="UNKN",
                 date_of_error="UNKN",
                 error_code=9999, old_data_value=9999,
                 new_data_value=9999, explanation=""):
        self.station_name = station_name
        self.station_type = station_type
        self.date_of_error = date_of_error
        self.error_code = error_code
        self.old_data_value = old_data_value
        self.new_data_value = new_data_value
        self.explanation = explanation

    def __str__(self):
        return "\n" + \
            "---------------------" + \
            "\nStation Name : " + str(self.station_name) + \
            "\nDate of Error : " + str(self.date_of_error) + \
            "\nError Code : " + str(self.error_code) + \
            "\nOld Data Value : " + str(self.old_data_value) + \
            "\nNew Data Value : " + str(self.new_data_value) + \
            "\nExplanation : " + str(self.explanation)

    __repr__ = __str__

    def get_code_type(self):
        return (self.error_code - 9000) / 100


def set_all_attr(err_list, attr, value):
    for err in err_list:
        setattr(err, attr, value)


def get_qc_type(error_num):
    qc_type = {
        9: "Temperature QC ",
        8: "Dewpoint QC ",
        7: "Precipitation QC ",
        6: "Pressure QC ",
        5: "Clouds QC ",
        4: "Wind QC ",
        3: "Visibility QC ",
        2: "Present Weather QC ",
        1: "Unrecognized elements QC "
    }
    return qc_type.get(error_num, "undefined qc")


def get_qc_type_by_string(obs_type):
    qc_type = {
        'temp': 9,
        'dewpoint': 8,
        'precip': 7,
        'pressure': 6,
        'clouds': 5,
        'wind': 4,
        'vis': 3,
        'present weather': 2,
        'UE': 1
    }
    return qc_type.get(obs_type, 0)


def stats(err_list, list_len=10):
    logging.info("----------------------------")
    logging.info("Total number of Errors: " + str(len(err_list)))

    for i in range(1, 10):

        num_errors = len(filter(
            lambda err: err.get_code_type() == i, err_list))
        num_type = get_qc_type(i)
        logging.info("Errors corrected during " + num_type + ": " + str(num_errors))

    mostoften = Counter(map(lambda err: err.station_name,
                            err_list)).most_common(list_len)
    logging.info("Stations most qc'd:")

    for i in mostoften:
        logging.info(i[0] + " -- " + str(i[1]))
    mostoften = Counter(map(lambda err: err.error_code,
                            err_list)).most_common(list_len)
    logging.info("Most errors of type:")
    for i in mostoften:
        logging.info(str(i[0]) + " -- " + str(i[1]))


def errors_of_type(err_list, err_str):
    return filter(
        lambda err: err.get_code_type == get_qc_type_by_string(err_str),
        err_list)


def errors_of_code(err_list, err_code):
    return filter(lambda err: err.error_code == err_code, err_list)
