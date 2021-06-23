
import pandas as pd
import calendar
import datetime
import os


# subclass of TextCalendar that displays calendar filled with data
class DataCalendar(calendar.TextCalendar):

    # takes dict with ISO dates as keys and corresponding data as values
    # returns string containing text calendar with dates filled with data
    def formatdata(self, data_dict):
        # start output string
        out = ''

        # get terminal width
        try:
            terminal_width = os.get_terminal_size().columns
        except OSError:
            terminal_width = 76

        # compute date box width
        max_len = max(map(lambda x: len(str(x)), data_dict.values()))
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
                    data_dict, counter.year, counter.month, date_width
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
    def formatmonthdata(self, data_dict, year, month, date_width=2):
        # start output string with month and weekdays header
        out = self.formatmonthname(year, month, date_width*7 + 6)
        out += '\n'*1
        out += self.formatweekheader(date_width)
        out += '\n'*1
        
        for week in self.monthdays2calendar(year, month):
            # get rid of empty days that the package uses
            week = [(d, wd) for (d, wd) in week if d != 0]
            for (day, day_of_wk) in week:
                ISO_date = datetime.date(year, month, day).isoformat()
                value = data_dict.get(ISO_date, '')
                s = str(value).center(date_width)
                if len(s) > date_width:
                    s = s[:date_width]
                out += s
                out += ' '
            out += '\n'*1

        return out

