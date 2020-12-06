
import prompt_toolkit as pt
import re

from .. import keywords
from .completion_util import get_filelist

class Completer(pt.completion.Completer):
    
    WordMatcher = re.compile(r'[^,:=;#\\\"\'\s]+')

    def get_completions(self, document, complete_event):

        d = document.get_word_before_cursor(Completer.WordMatcher)

        # We are in the first word
        if document.find_start_of_previous_word() is None or \
            document.get_start_of_line_position() == document.find_start_of_previous_word() and \
            d:
            for c in keywords.command_keywords:
                if c.startswith(d):
                    yield pt.completion.Completion(c + ' ', start_position=-len(d))

        # Otherwise
        else:
            # Filenames: 
            if d.startswith('\'') or d.startswith('"'):
                for c in get_filelist(d):
                    if c.startswith(d):
                        yield pt.completion.Completion(c, start_position=-len(d))
                return

            # Style keyword must be satisfied first
            for c in keywords.all_style_keywords:
                if c.startswith(d):
                    yield pt.completion.Completion(c + '=', start_position=-len(d))

            # Alternatively, style values may be matched in pattern xxx=

            

            # (Experimental) command-specified completion
            #match = self.WordMatcher.match(document.text())
            #if match:
            #    command = match.group()
                