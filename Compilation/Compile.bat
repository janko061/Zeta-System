@echo off

bml2latex --no-tree -o ..\Sistem.tex ..\BML\SistemBML.txt
python ..\tools\bml_format.py ..\Sistem.tex ..\Sistem.tex

bml2html --no-tree -o Sistem.html ..\BML\SistemBML.txt

REM latexmk -pdf -output-directory=Compilation Sistem.tex

latexmk -pdf ..\Sistem.tex

REM move .\Compilation\Sistem.pdf .

echo Done!