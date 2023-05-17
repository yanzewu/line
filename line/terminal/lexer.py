
import re
from collections import deque

from ..vm import LineDebugInfo
from ..errors import LineParseError


class Lexer:

    STATE_EMPTY = 0
    STATE_HOLD = 1
    STATE_BRACKET = 2

    STRING_DOUBLEQUOTE = re.compile(r'(\\.|[^\\\"])*\"')
    STRING_SINGLEQUOTE = re.compile(r'(\\.|[^\\\'])*\'') 

    def run(self, fetch_nextline):
        """ 
        When line is not enough, will call fetch_nextline(forced:bool) -> [str|None]
            fetch_nextline() should be blocking; It returns None if no new line is available.
            `forced' just changes the PS style, to inform user that the new line is required.
        Returns a generator of tokens.
        """
        self.buffer = fetch_nextline(False)
        self.tokens = deque()
        self.token_poses = []
        self.head = 0
        self.tail = 0
        self.state = Lexer.STATE_EMPTY
        self.lineid = 0
        self.unfinished_token = ''
        self.unfinished_token_pos = (0, 0)

        self.bracket_stack = []

        if self.buffer is None:
            yield self.tokens.copy(), self.token_poses.copy()
            return

        while True:
            if self.buffer is None:
                break
            
            if self.head >= len(self.buffer):
                if self.state == Lexer.STATE_BRACKET:
                    raise LineParseError("Bracket does not match")
                self.reduce()
                yield self.tokens.copy(), self.token_poses.copy()

                self.clear_tokens()
                self.update_buffer(fetch_nextline)
                if self.buffer is None:
                    break
                elif self.buffer == '':
                    continue

            c = self.buffer[self.head]
            if c in '"\'':
                self.reduce()
                self.match_string(fetch_nextline)
                self.reduce()
            elif self.buffer[self.head:self.head+2] == '${' or \
                    self.buffer[self.head:self.head+2] == '$(' or \
                    self.buffer[self.head:self.head+3] == '$!(':
                self.reduce()
                if self.bracket_stack:
                    raise LineParseError("Special brackets cannot be nested")
                else:
                    n = 2 if self.buffer[self.head+1] in '({' else 3
                    self.bracket_stack.append(self.buffer[self.head + n - 1])
                    self.shift(n)
                    self.reduce()
                    self.state = Lexer.STATE_BRACKET
            elif c in ')}' and self.state == Lexer.STATE_BRACKET:
                if self.is_paired(self.bracket_stack[-1], c):
                    self.bracket_stack.pop()
                    self.shift()
                    self.reduce()
                    if not self.bracket_stack:
                        self.state = Lexer.STATE_EMPTY
                else:
                    raise LineParseError("Bracket does not match")
            elif c in '({' and self.state == Lexer.STATE_BRACKET:
                self.bracket_stack.append(c)
                self.shift()
                self.reduce()
            elif c in ' \t':
                self.reduce()
                if self.state == Lexer.STATE_BRACKET:
                    self.shift()
                else:
                    self.inc()
            elif c in ',=:' and self.state != Lexer.STATE_BRACKET:
                self.reduce()
                self.tokens.append(c)
                self.token_poses.append((self.lineid, self.head))
                self.inc()
            elif c == '#':
                self.reduce()
                yield self.tokens.copy(), self.token_poses.copy()

                self.clear_tokens()
                self.update_buffer(fetch_nextline)
            elif c == '\\':
                self.reduce()
                self.update_buffer(fetch_nextline, True)
            elif c in ';\n':
                self.reduce()
                yield self.tokens.copy(), self.token_poses.copy()

                self.clear_tokens()
                self.inc()
            else:
                self.shift()

    def match_string(self, fetch_nextline):
        quote = self.buffer[self.head]
        self.head += 1
        matcher = Lexer.STRING_DOUBLEQUOTE if quote == '"' else Lexer.STRING_SINGLEQUOTE
        m = matcher.match(self.buffer, self.head)

        self.unfinished_token = ''
        self.unfinished_token_pos = (self.lineid, self.tail)

        while m is None:
            self.unfinished_token += self.buffer[self.tail:] + '\n'
            self.update_buffer(fetch_nextline, True)
            m = matcher.match(self.buffer, self.head)

        self.head = m.end()
        if self.state != Lexer.STATE_BRACKET:
            self.state = Lexer.STATE_HOLD

    def is_paired(self, a, b):
        return b == {'(':')', '[':']', '{':'}'}[a]


    def reduce(self):
        if self.state != Lexer.STATE_EMPTY:
            if self.unfinished_token:
                if self.state == Lexer.STATE_BRACKET:
                    self.tokens[-1] += self.unfinished_token + self.buffer[:self.head]
                else:
                    self.tokens.append(self.unfinished_token + self.buffer[:self.head])
                    self.token_poses.append(self.unfinished_token_pos)
                self.unfinished_token = ''
            else:
                if self.state == Lexer.STATE_BRACKET:
                    self.tokens[-1] += self.buffer[self.tail:self.head]
                else:
                    self.tokens.append(self.buffer[self.tail:self.head])
                    self.token_poses.append((self.lineid, self.tail))

            if self.state != Lexer.STATE_BRACKET:
                self.state = Lexer.STATE_EMPTY

        self.tail = self.head

    def shift(self, n=1):
        if self.state == Lexer.STATE_EMPTY:
            self.tail = self.head
            self.state = Lexer.STATE_HOLD
        self.head += n

    def inc(self):
        self.head += 1
        self.tail = self.head

    def update_buffer(self, fetch_nextline, forced=False):
        self.buffer = fetch_nextline(forced)
        if self.buffer is None and forced:
            raise LineParseError('Incomplete command')

        self.lineid += 1
        self.head = 0
        self.tail = 0

    def clear_tokens(self):
        self.tokens.clear()
        self.token_poses.clear()
     

def split(text:str):
    has_fetched = [False]
    def fetch_nextline(forced):
        if not has_fetched[0]:
            has_fetched[0] = True
            return text
        else:
            return

    return next(Lexer().run(fetch_nextline))
