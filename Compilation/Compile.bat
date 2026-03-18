@echo off

bml2latex -o ..\Sistem.tex ..\BML\SistemBML.txt

bml2html -o Sistem.html ..\BML\SistemBML.txt

REM latexmk -pdf -output-directory=Compilation Sistem.tex

latexmk -pdf ..\Sistem.tex

REM move .\Compilation\Sistem.pdf .

echo Done!