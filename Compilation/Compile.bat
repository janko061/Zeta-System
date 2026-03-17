@echo off

bml2latex -o Sistem.tex .\BML\SistemBML.txt

latexmk -pdf -output-directory=Compilation Sistem.tex

move .\Compilation\Sistem.pdf .

echo Done!