#! /usr/bin/python
# coding=utf-8

import datetime
from datetime import datetime as d
from pprint import pprint
import unicodecsv
import re

from tp import GCalendarEntry


LESSONS = [
    {'begin': '08:30:00 AM', 'end': '10:05:00 AM'},
    {'begin': '10:15:00 AM', 'end': '11:50:00 AM'},
    {'begin': '12:00:00 PM', 'end': '01:35:00 PM'},
    {'begin': '01:50:00 PM', 'end': '03:25:00 PM'},
    {'begin': '03:40:00 PM', 'end': '05:15:00 PM'},
    {'begin': '05:25:00 PM', 'end': '07:00:00 PM'},
    {'begin': '07:10:00 PM', 'end': '08:45:00 PM'},
]

class TimeTableEntry:
    @staticmethod
    def str_to_time(s):
        return d.strptime(s, "%I:%M:%S %p")

    def __init__(self, data):
        self.day = data['day']
        self.nomdom = data['nomdom']
        self.discipline = data['discipline']
        self.location = data['location']
        self.type = data['type']

        self.lessons = data['lessons']
        m = re.match(r'(.+)-(.+)', self.lessons)
        if m is None:
            m = re.match('\s*(\d+)\s*', self.lessons)
            if m is None or m.group(1) is None:
                raise Exception("Wrong lessons format: %s" % self.lessons)
            else:
                first_lesson = LESSONS[int(m.group(1)) - 1]
                self.begin_time = self.str_to_time(first_lesson['begin'])
                self.end_time = self.str_to_time(first_lesson['end'])
        else:
            m2 = re.match('\s*(\d+)\s*-\s*(\d+)\s*', self.lessons)
            if m2 is None or m2.group(1) is None or m2.group(2) is None:
                if m.group(1) is None or m.group(2) is None:
                    raise Exception("Wrong lessons format: %s" % self.lessons)
                self.begin_time = self.str_to_time(m.group(1))
                self.end_time = self.str_to_time(m.group(2))
            else:
                self.begin_time = self.str_to_time(LESSONS[int(m2.group(1)) - 1]['begin'])
                self.end_time = self.str_to_time(LESSONS[int(m2.group(2)) - 1]['end'])


class BaumanParser:
    weekdays = {
        'mon': 0,
        'tue': 1,
        'wed': 2,
        'thu': 3,
        'fri': 4,
        'sat': 5,
        'sun': 6
    }

    types = {
        'lecture': u'L',
        'seminar': u'S',
        'mixed': u'LS',
        'lab': u'Lab'
    }

    nomdom = ['nom', 'dom']

    def __init__(self, first_day, last_day):
        self.first_day = d.strptime(first_day, "%d.%m.%Y")
        self.last_day = d.strptime(last_day, "%d.%m.%Y")

    def parse(self, input_file, output_file):
        timetable = list(self._read_file(input_file))

        current_day = self.first_day

        def next_nomdom(nomdom_index):
            new_index = (nomdom_index + 1) % len(self.nomdom)
            return self.nomdom[new_index], new_index

        (nomdom, nomdom_index) = next_nomdom(-1)

        with open(output_file, "w") as f:
            w = unicodecsv.writer(f, encoding='utf-8')

            w.writerow(GCalendarEntry.header_row)

            very_last_day = self.last_day + datetime.timedelta(days=1)
            while current_day != very_last_day:

                if current_day.weekday() == self.weekdays['sun']:
                    (nomdom, nomdom_index) = next_nomdom(nomdom_index)
                else:
                    for entry in timetable:
                        if self.weekdays[entry.day] == current_day.weekday() and \
                                (entry.nomdom == 'all' or entry.nomdom == nomdom):
                            gentry = self._construct_gentry(entry, current_day)
                            w.writerow(gentry.to_tuple())

                current_day += datetime.timedelta(days=1)

    def _read_file(self, input_file):
        with open(input_file, mode='r') as f:
            r = unicodecsv.DictReader(f)
            for row in r:
                yield TimeTableEntry(row)

    def _construct_gentry(self, entry, current_day):
        start_date = current_day.strftime('%m/%d/%y')

        start_time = entry.begin_time.strftime('%H:%M:%S')
        end_time = entry.end_time.strftime('%H:%M:%S')

        gentry = GCalendarEntry(subject=self.types[entry.type] + ' ' + entry.discipline,
                                start_date=start_date,
                                start_time=start_time,
                                end_date=start_date,
                                end_time=end_time,
                                all_day=False,
                                description='',
                                location=entry.location,
                                is_private=True)
        return gentry


if __name__ == "__main__":
    parser = BaumanParser("01.09.2015", "31.12.2015")
    parser.parse("bauman.csv", "out_bauman.csv")
    print 'ok'
