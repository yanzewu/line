
set -e

cd ../
printf "\n--------- testing lex ----------\n"
python -m line -d test/test-lex.line
printf "\n--------- testing vm ----------\n"
python -m line -d test/test-vm.line
printf "\n--------- testing plot ----------\n"
python -m line -d test/test-plot.line
printf "\n--------- testing hist ----------\n"
python -m line -d test/test-hist.line
printf "\n--------- testing expr ----------\n"
python -m line -d test/test-expr.line a
printf "\n--------- testing stdin ----------\n"
cat example/test-data.txt | python -m line -d test/test-stdin.line 
printf "\n--------- testing style ----------\n"
python -m line -d test/test-style.line
printf "\n--------- testing element ----------\n"
python -m line -d test/test-element.line
printf "\n--------- testing figure ----------\n"
python -m line -d test/test-figure.line
printf "\n--------- testing io ----------\n"
python -m line -d test/test-io.line

echo "Success"