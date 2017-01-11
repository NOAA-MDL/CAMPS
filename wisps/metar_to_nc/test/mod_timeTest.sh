#!/bin/bash
echo "pressure qc time test" 
python -m timeit -s 'import qc_new.timeTest as tt' 'tt.pressure_mod()' 
echo "winds time test" 
python -m timeit -s 'import qc_new.timeTest as tt' 'tt.winds_mod()' 
echo "clouds time test" 
python -m timeit -s 'import qc_new.timeTest as tt' 'tt.clouds_mod()' 
