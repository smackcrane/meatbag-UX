
class tab_completer:
    def __init__(self, options):
        self.options = options
        self.matches = []

    def __call__(self, text, state):
        if state == 0:
            self.matches = [opt for opt in self.options if opt.startswith(text)]
            return self.matches[0]
        elif state < len(self.matches):
            return self.matches[state]
        else:
            return None


