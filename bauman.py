#! /usr/bin/python
# coding=utf-8

import datetime
from datetime import datetime as d
import unicodecsv

from tp import GCalendarEntry


class TimeTableEntry:
    def __init__(self, data):
        self.day = data['day']
        self.nomdom = data['nomdom']
        self.discipline = data['discipline']
        self.location = data['location']
        self.type = data['type']
        self.begin_time = d.strptime(data['begin'], "%I:%M:%S %p")
        self.end_time = d.strptime(data['end'], "%I:%M:%S %p")


class BaumanParser:
    first_day = d.strptime("01.09.2014", "%d.%m.%Y")
    last_day = d.strptime("31.12.2014", "%d.%m.%Y")

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

    def __init__(self):
        pass

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
    parser = BaumanParser()
    parser.parse("bauman.csv", "out_bauman.csv")
    print 'hi'