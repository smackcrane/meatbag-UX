import pandas as pd
try:
    import gnureadline as readline
except ImportError:
    import readline

class tab_completer:
    def __init__(self, options):
        self.options = list(set([s for s in options if type(s)==str]))
        self.matches = []

    def __call__(self, text, state):
        if state == 0:
            line = readline.get_line_buffer()
            skip = line.rfind(' ') + 1
            self.matches = [opt[skip:] for opt in self.options if opt.startswith(line)] or [opt for opt in self.options if opt.startswith(text)]
            return self.matches[0]
        elif state < len(self.matches):
            return self.matches[state]
        else:
            return None


