
set -e

cd ../
python -m line -d test/test-lex.line
python -m line -d test/test-plot.line
python -m line -d test/test-hist.line
python -m line -d test/test-expr.line a
python -m line -d test/test-style.line
python -m line -d test/test-element.line
python -m line -d test/test-figure.line
python -m line -d test/test-io.line

echo "Success"