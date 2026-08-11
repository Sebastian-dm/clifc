REM Usage: cli.py crop [OPTIONS] INPUT_FILE P1 P2
REM   Crop an IFC file using two rectangle corners.
REM   P1 and P2 should be given as quoted coordinate pairs:
REM       clifc crop model.ifc "627579.000 1147842.900" "627608.000 1147868.100"
REM Options:
REM   -o, --output_file TEXT  Output IFC file
REM   -v, --verbose           Enable verbose output
REM   --help                  Show this message and exit.

@echo off
cd /d "%~dp0/.."
call ".venv/Scripts/activate"
python "src/clifc/cli.py" crop^
       -o cropped.ifc^
       models/KKU_K23_S1_N01.ifc^
       "627506.000 1147902.900" "627538.000 1147884.100"
pause
