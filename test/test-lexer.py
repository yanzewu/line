import sys
sys.path.append('..')

from line.terminal.lexer import Lexer
from collections import deque

def test_a_session(text, answer):
    count = [-1]
    def fetch_nextline(forced):
        count[0] += 1
        return text[count[0]]

    lexer = Lexer()
    g = lexer.run(fetch_nextline)
    for j in answer:
        k = next(g)
        print(k)
        assert j == k


if __name__ == '__main__':

    # normal cases
    test_a_session(["a b  c\t $de=,(f'g df''h\\'i'j # klm"], [
        (deque(['a', 'b', 'c', '$de', '=', ',', '(f', "'g df'", "'h\\'i'", 'j']), [(0, 0), (0, 2), (0, 5), (0, 8), (0, 11), (0, 12), (0, 13), (0, 15), (0, 21), (0, 27)])
    ])

    # multiple lines
    test_a_session(["ab\\", "c \\", " d;; 'e ", "f' 'g", "", "h'"], [
        (deque(['ab', 'c', 'd']), [(0, 0), (1, 0), (2, 1)]),
        (deque([]), []),
        (deque(["'e \nf'", "'g\n\nh'"]), [(2, 5), (3, 3)])
    ])

    # brackets
    test_a_session(["a$(b{ c}(d)) $!( e \\", "f) ${g ' h", "i'} "], [
        (deque(['a', '$(b{c}(d))', '$!(ef)', "${g' h\ni'}"]), [(0, 0), (0, 1), (0, 13), (1, 3)])
    ])

    test_a_session(["$('abc') 'def'"], [(deque(["$('abc')", "'def'"]), [(0, 0), (0, 9)])])

    print('Success')
