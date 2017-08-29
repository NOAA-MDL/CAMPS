#!/usr/bin/env python
import os
import sys
relative_path = os.path.abspath(
    os.path.dirname(os.path.realpath(__file__)) + "/../..")
sys.path.insert(0, relative_path)
import mospred.parse_pred as pp
import mospred.read_pred as rp
import registry.util as cfg
import pdb


def test_separate_entries():
    ret = pp.separate_entries("1600h")
    assert ret == {'time' : 5760000}
    ret = pp.separate_entries("1600 hours")
    assert ret == {'time' : 5760000}
    ret = pp.separate_entries("1600 hours average")
    assert ret == {'time' : 5760000, 'cell_method' : 'mean'}
    ret = pp.separate_entries("7days average")
    assert ret == {'time' : 604800, 'cell_method' : "mean"}
    ret = pp.separate_entries("1600s average")
    print ret
    assert ret == {"time" : 1600, 'cell_method' : "mean"}


def test_get_cell_method():
    assert pp.cell_method(" difference") == 'difference'
    assert pp.cell_method(" dif") != 'difference'
    assert pp.cell_method(" avg") == 'mean'
    assert pp.cell_method("mean accum") == 'mean'
    assert pp.cell_method("temp maxim") == 'maximum'
    assert pp.cell_method("difference") == 'difference'
    assert pp.cell_method("difference") == 'difference'

def test_parse_range():
    out_dict = rp.parse_range('2013100100-2014033100,12h')
    
def test_get_variable():
    var_dict = cfg.read_yaml('test_pred.yml')
    rp.get_variable(var_dict[0])

def test_get_time_multiplier():
    assert pp.get_time_multiplier("days") == 86400
    assert pp.get_time_multiplier("h") == 3600
    assert pp.get_time_multiplier("hours") == 3600
    assert pp.get_time_multiplier("min") == 60
    assert pp.get_time_multiplier("s") == 1


def test_observedProperty():
    try:
        pp.observedProperty("wind_speed")
        assert False  # should not get here
    except KeyError:
        pass  # All good.
    assert pp.observedProperty("Temp") is not None
    assert pp.observedProperty("Gust") == 'StatPP/Data/Met/Moment/Gust'


def test_vertical_coordinate():
    ret = pp.vertical_coordinate("10-15m diff")
    assert ret['layer1'] == 10
    assert ret['layer2'] == 15
    assert ret['units'] == 'm'
    assert ret['cell_method'] == 'difference'
    ret = pp.vertical_coordinate('0')
    assert ret['layer1'] == 0

if __name__ == "__main__":

    test_separate_entries()
    test_get_cell_method()
    test_observedProperty()
    test_get_time_multiplier()
    test_vertical_coordinate()
    test_parse_range()
    test_get_variable()
    
    print "PASSED mospred"
