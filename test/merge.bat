@echo off
REM Usage: cli.py merge [OPTIONS] [PATHS]...
REM   Merge IFC objects from multiple IFC files into one IFC model.
REM 
REM Options:
REM   -o, --output-file TEXT  Output merged IFC file
REM   -v, --verbose           Enable verbose output
REM   --help                  Show this message and exit.

cd /d "%~dp0/.."
call ".venv/Scripts/activate"
python "src/clifc/cli.py" merge^
	-o test/merged.ifc^
	models/KKU_K23_S1_N01.ifc^
	models/KKU_K23_S2_N01.ifc
pause
