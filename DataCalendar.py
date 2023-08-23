
import math
import pandas as pd
import calendar
import datetime
import os

# utility to strip ANSI escape codes
# thanks https://stackoverflow.com/a/14889588
import re
strip_ANSI_pat = re.compile(r"""
    \x1b     # literal ESC
    \[       # literal [
    [;\d]*   # zero or more digits or semicolons
    [A-Za-z] # a letter
    """, re.VERBOSE).sub

def strip_ANSI(s):
    return strip_ANSI_pat("", s)

# subclass of TextCalendar that displays calendar filled with data
class DataCalendar(calendar.TextCalendar):

    # takes dict with ISO dates as keys and corresponding data as values
    # returns string containing text calendar with dates filled with data
    def formatdata(self, data_dict, visualize):
        # start output string
        out = ''

        # get terminal width
        try:
            terminal_width = os.get_terminal_size().columns
        except OSError:
            terminal_width = 76

        # compute date box width
        val_length = lambda x: len(
                strip_ANSI(str(visualize(x, dataset=data_dict)))
                )
        max_len = max(map(val_length, data_dict.values()))
        date_width = min((terminal_width-6) // 7, max_len)
        # compute total output width
        out_width = date_width*7 + 6

        # get first and last dates
        dates = list(data_dict.keys())
        dates.sort()
        first = datetime.date.fromisoformat(dates[0])
        last = datetime.date.fromisoformat(dates[-1])

        # add first year header
        out += str(first.year).center(out_width)
        out += '\n'*2

        # iterate through months and add each to output
        counter = datetime.date(first.year, first.month, 1)
        while counter <= last:
            # format one month of data
            out += self.formatmonthdata(
                    data_dict, counter.year, counter.month, date_width,
                    visualize
                    )
            # increment counter
            if counter.month == 12:
                counter = datetime.date(counter.year+1, 1, 1)
                if counter <= last:
                    # add year header
                    out += '\n'*2
                    out += str(counter.year).center(out_width)
                    out += '\n'*2
            else:
                counter = datetime.date(counter.year, counter.month+1, 1)

        return out

    # takes dict with ISO dates as keys and corresponding data as values
    # as well as year and month and width of date box
    # prints text calendar of single month with dates filled with data
    def formatmonthdata(
            self, data_dict, year, month, date_width,
            visualize
            ):
        # start output string with month and weekdays header
        out = self.formatmonthname(year, month, date_width*7 + 6)
        out += '\n'*1
        out += self.formatweekheader(date_width)
        out += '\n'*1
        
        for week in self.monthdays2calendar(year, month):
            for (day, day_of_wk) in week:
                # handle 'empty' days, before month starts or after it ends
                if day == 0:
                    out += ' '*date_width
                    out += ' '
                    continue
                ISO_date = datetime.date(year, month, day).isoformat()
                value = data_dict.get(ISO_date, '')
                # extract relevant information for visualization
                value = visualize(value, dataset=data_dict)
                s = str(value).center(date_width)
                if len(strip_ANSI(s)) > date_width:
                    s = s[:date_width]
                out += s
                out += ' '
            out += '\n'*1

        return out

    # visualization function
    # identity
    def identity(self, value, **kwargs):
        return value

    # visualization function
    # returns a solid block if input is true, else 'empty block' i.e. spaces
    def truth_blocks(self, value, **kwargs):
        return '\u2588'*2 if value else '\u2591'*2

    # visualization function
    # returns blocks with brightness proportional to value
    def value_blocks(self, value, dataset):
        # hacky way to get rid of nan
        vals = [x for x in dataset.values() if x >=0 or x <=0]
        big = max(vals)
        small = min(vals)
        blocks = [f'\033[38;5;{i}m\u2588\u2588\033[0m' for i in range(236, 256)]
        blocks = ['\u2591'*2]+blocks
        n = len(blocks)
        cutoffs = [small+(big-small)*i/n for i in range(n-1)]
        bucket = 0
        while value and bucket < n-1 and value >= cutoffs[bucket]:
            bucket += 1
        return blocks[bucket]

    # visualization function
    # returns blocks with brightness proportional to logarithm of value
    def log_value_blocks(self, value, dataset):
        # restrict to positive values and take log
        vals = [math.log(x) for x in dataset.values() if x > 0]
        big = max(vals)
        small = min(vals)
        blocks = [f'\033[38;5;{i}m\u2588\u2588\033[0m' for i in range(236, 256)]
        blocks = ['\u2591'*2]+blocks
        n = len(blocks)
        cutoffs = [small+(big-small)*i/n for i in range(n-1)]
        bucket = 0
        # god forgive me
        while value and value > 0 and bucket < n-1 and math.log(value) >= cutoffs[bucket]:
            bucket += 1
        return blocks[bucket]

    # visualization function
    # returns blocks colored by value, roughly blue -> rainbow -> white
    def color_blocks(self, value, dataset):
        # hacky way to get rid of nan
        vals = [x for x in dataset.values() if x >=0 or x <=0]
        big = max(vals)
        small = min(vals)
        colormap = [ [0,g,255] for g in range(256) ] + \
                   [ [0,255,255-b] for b in range(256) ] + \
                   [ [r,255,0] for r in range(256) ] + \
                   [ [255,255-g,0] for g in range(256) ] + \
                   [ [255,w,w] for w in range(256) ]
        blocks = [f'\033[38;2;{r};{g};{b}m\u2588\u2588\033[0m' for [r,g,b] in colormap]
        blocks = ['\u2591'*2]+blocks
        n = len(blocks)
        cutoffs = [small+(big-small)*i/n for i in range(n-1)]
        bucket = 0
        while value and bucket < n-1 and value >= cutoffs[bucket]:
            bucket += 1
        return blocks[bucket]

    # visualization function
    # returns blocks colored by log value, roughly blue -> rainbow -> white
    def log_color_blocks(self, value, dataset):
        # restrict to positive values and take log
        vals = [math.log(x) for x in dataset.values() if x > 0]
        big = max(vals)
        small = min(vals)
        colormap = [ [0,g,255] for g in range(256) ] + \
                   [ [0,255,255-b] for b in range(256) ] + \
                   [ [r,255,0] for r in range(256) ] + \
                   [ [255,255-g,0] for g in range(256) ] + \
                   [ [255,w,w] for w in range(256) ]
        blocks = [f'\033[38;2;{r};{g};{b}m\u2588\u2588\033[0m' for [r,g,b] in colormap]
        blocks = ['\u2591'*2]+blocks
        n = len(blocks)
        cutoffs = [small+(big-small)*i/n for i in range(n-1)]
        bucket = 0
        # god forgive me
        while value and value > 0 and bucket < n-1 and math.log(value) >= cutoffs[bucket]:
            bucket += 1
        return blocks[bucket]

