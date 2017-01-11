#!/bin/bash
echo $1
if [[ $1 ]]; then
echo "clouds qc time test" 
python -m timeit -s 'import qc.timeTest as tt' 'tt.clouds()' 
echo "precip qc time test" 
python -m timeit -s 'import qc.timeTest as tt' 'tt.precip()' 
echo "temp qc time test" 
python -m timeit -s 'import qc.timeTest as tt' 'tt.temp()' 
fi
echo
echo "winds qc time test" 
python -m timeit -s 'import qc.timeTest as tt' 'tt.winds()' 
echo
echo "pressure qc time test" 
python -m timeit -s 'import qc.timeTest as tt' 'tt.pressure()' 
echo "weather qc time test" 
python -m timeit -s 'import qc.timeTest as tt' 'tt.weather()' 
