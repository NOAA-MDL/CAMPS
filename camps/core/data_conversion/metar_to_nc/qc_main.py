import logging
import sys
import os
import qc_clouds
import qc_precip
import qc_temp
import qc_winds
import qc_main
import qc_pressure
import qc_weather
import qc_error
import pdb
import time


def qc(station_dict,err_file=None):
    all_errors = []

    logging.info("Starting QC...")
    station_list = station_dict.values()

    start = time.time()
    logging.info("QC Temperature")
    all_errors += qc_temp.qc_temp(station_list)
    end = time.time()
    logging.info(end - start)

    start = time.time()
    logging.info("QC Pressure")
    all_errors += qc_pressure.qc_pressure(station_list)
    end = time.time()
    logging.info(end - start)

    start = time.time()
    logging.info("QC Clouds")
    all_errors += qc_clouds.qc_clouds(station_list)
    end = time.time()
    logging.info(end - start)

    start = time.time()
    logging.info("QC Winds")
    all_errors += qc_winds.qc_winds(station_list)
    end = time.time()
    logging.info(end - start)

    start = time.time()
    logging.info("QC Weather")
    all_errors += qc_weather.qc_weather(station_list)
    end = time.time()
    logging.info(end - start)

    start = time.time()
    logging.info("QC Precip")
    all_errors += qc_precip.qc_precip(station_list)
    end = time.time()
    logging.info(end - start)

    all_errors += qc_error.all_qc_errors

    type(all_errors)

    tmp_errors = []
    for i in all_errors:
        if i is not None:
            try:
                if len(i) > 0:
                    tmp_errors += i
            except:
                tmp_errors.append(i)

    all_errors = tmp_errors

    qc_error.stats(all_errors, 50)
    all_errors = sorted(all_errors, key=lambda err: err.station_name)

    with open(err_file, 'w+') as efo:
        for i in all_errors:
            efo.write(str(i))

    return station_dict

#def flatten(l): return [item for sublist in l for item in sublist]
