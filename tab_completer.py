import pandas as pd

class tab_completer:
    def __init__(self, options):
        self.options = pd.unique([s for s in options if type(s)==str])
        self.matches = []

    def __call__(self, text, state):
        if state == 0:
            self.matches = [opt for opt in self.options if opt.startswith(text)]
            return self.matches[0]
        elif state < len(self.matches):
            return self.matches[state]
        else:
            return None


