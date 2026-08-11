REM Usage: cli.py propcheck [OPTIONS] [PATHS]...
REM   Check IFC files against property rules defined in a YAML file.
REM Options:
REM   -r, --rulespath PATH     YAML rules file  [required]
REM   -o, --outputfolder TEXT  Folder to output reports to (default: current folder)
REM   -s, --schemapath TEXT    Path to override the default JSON schema file for rules validation
REM   -t, --templatepath TEXT  Path to override the default HTML template for report generation
REM   -c, --csv_out            Export results to CSV file
REM   -a, --all                Include all (also passing) rows in CSV
REM   -v, --verbose            Enable verbose output
REM   --help                   Show this message and exit.

@echo off
cd /d "%~dp0/.."
call ".venv/Scripts/activate"
python "src/clifc/cli.py" propcheck^
	-r "config/rulesExample.yaml"^
	-o test^
	models/KKU_K23_S1_N01.ifc
pause
