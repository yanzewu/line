@echo off
python test-lexer.py
python test-plot.py
cd ../
echo. & echo "--------- testing lex ----------" & echo.
python -m line -d test/test-lex.line
if %errorlevel% neq 0 exit /b %errorlevel%
echo. & echo "--------- testing vm ----------" & echo.
python -m line -d test/test-vm.line
if %errorlevel% neq 0 exit /b %errorlevel%
echo. & echo "--------- testing plot ----------" & echo.
python -m line -d test/test-plot.line
if %errorlevel% neq 0 exit /b %errorlevel%
echo. & echo "--------- testing hist ----------" & echo.
python -m line -d test/test-hist.line
if %errorlevel% neq 0 exit /b %errorlevel%
echo. & echo "--------- testing expr ----------" & echo.
python -m line -d test/test-expr.line a
if %errorlevel% neq 0 exit /b %errorlevel%
echo. & echo "--------- testing stdin ----------" & echo.
cat example/test-data.txt | python -m line -d test/test-stdin.line 
if %errorlevel% neq 0 exit /b %errorlevel%
echo. & echo "--------- testing style ----------" & echo.
python -m line -d test/test-style.line
if %errorlevel% neq 0 exit /b %errorlevel%
echo. & echo "--------- testing element ----------" & echo.
python -m line -d test/test-element.line
if %errorlevel% neq 0 exit /b %errorlevel%
echo. & echo "--------- testing figure ----------" & echo.
python -m line -d test/test-figure.line
if %errorlevel% neq 0 exit /b %errorlevel%
echo. & echo "--------- testing io ----------" & echo.
python -m line -d test/test-io.line
if %errorlevel% neq 0 exit /b %errorlevel%

echo Success