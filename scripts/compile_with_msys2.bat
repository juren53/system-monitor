@echo off
echo Adding MSYS2 to PATH for compilation...
set PATH=C:\msys64\mingw64\bin;%PATH%
echo MSYS2 added. Ready to compile.
echo Current Python:
where python
REM Add your compile commands here
REM mingw32-make
REM gcc -o program.exe source.c