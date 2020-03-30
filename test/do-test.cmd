@echo off
cd ../
python -m line -d test/test-lex.line
if %errorlevel% neq 0 exit /b %errorlevel%
python -m line -d test/test-vm.line
if %errorlevel% neq 0 exit /b %errorlevel%
python -m line -d test/test-plot.line
if %errorlevel% neq 0 exit /b %errorlevel%
python -m line -d test/test-hist.line
if %errorlevel% neq 0 exit /b %errorlevel%
python -m line -d test/test-expr.line a
if %errorlevel% neq 0 exit /b %errorlevel%
python -m line -d test/test-style.line
if %errorlevel% neq 0 exit /b %errorlevel%
python -m line -d test/test-element.line
if %errorlevel% neq 0 exit /b %errorlevel%
python -m line -d test/test-figure.line
if %errorlevel% neq 0 exit /b %errorlevel%
python -m line -d test/test-io.line
if %errorlevel% neq 0 exit /b %errorlevel%

echo Success