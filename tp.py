#! /usr/bin/python
# coding=utf-8

import json
import time
import re
import unicodecsv
import requests
from BeautifulSoup import BeautifulSoup


class GCalendarEntry:
    header_row = tuple(
        "Subject,Start Date,Start Time,End Date,End Time,All Day Event,Description,Location,Private".split(','))

    def __init__(self, subject, start_date, start_time, end_date, end_time, all_day, description, location, is_private):
        self.subject = subject
        self.start_date = start_date
        self.start_time = start_time
        self.end_date = end_date
        self.end_time = end_time
        self.all_day = all_day
        self.description = description
        self.location = location
        self.is_private = is_private

    def to_tuple(self):
        return (self.subject, self.start_date, self.start_time,
                self.end_date, self.end_time, self.all_day, self.description, self.location, self.is_private)


class TimeTableLessonEntry:
    type_entity = 'lesson'

    def __init__(self, data):
        self.id = data['id']
        self.start = data['start']
        self.end = data['end']
        self.title = data['title']
        self.short_title = data['short_title']
        self.auditorium_title = data['auditorium_title']
        self.schedule_id = data['schedule_id']
        self.lesson_id = data['lesson_id']
        self.schedule_date = data['schedule_date']
        self.selection_id = data['selection_id']
        self.type_title = data['type_title']
        self.number = data['number']
        self.auditorium_number = data['auditorium_number']
        self.is_important = data['is_important']
        self.is_optional = data['is_optional']
        self.event_title = data['event_title']
        self.lesson_title = data['lesson_title']
        self.lesson_topic = data['lesson_topic']
        self.subgroups = data['subgroups']


class TimetableParser:
    title_prefix = u"ТП "
    schedule_url = 'https://tech-mail.ru/schedule/'
    calendar_url = 'https://tech-mail.ru/schedule/calendar'

    def __init__(self, csv_filename, group_name):
        self.csv_filename = csv_filename
        self.group_name = group_name

    def parse(self):
        s = requests.session()
        schedule_page = s.get(self.schedule_url).text

        parsed_page = BeautifulSoup(schedule_page)
        security_key = self._get_security_key(parsed_page)
        group_id = self._get_group_id(parsed_page, self.group_name)

        params = {
            'start': '1420070400',
            'end': '1435957200',
            'filter[subgroup_id][]': group_id,
            'filter[type_id][]': 'all',
            'filter[discipline_id][]': 'all',
            'security_ls_key': security_key,
            'withCustomEvent': True
        }

        calendar_json = s.get(self.calendar_url, params=params).text
        self._parse_json(calendar_json)

    @staticmethod
    def _get_security_key(parsed_page):
        script_tag = parsed_page.head.find('script').text
        script_lines = script_tag.split('\n')
        security_key = None
        for line in script_lines:
            line = line.strip()
            m = re.match(r".*LIVESTREET_SECURITY_KEY\s*=\s*'(.*)'.*", line)
            if m is not None:
                security_key = m.group(1)
                break

        if security_key is None:
            raise Exception("Couldn't find security key")

        return security_key

    @staticmethod
    def _get_group_id(parsed_page, group_name):
        groups = parsed_page.body.findAll(attrs={'class': re.compile(r".*\bsl-filter_group\b.*")})[0]\
                                 .findAll(attrs={'class': re.compile(r".*\bselectInput-options\b.*")})[0]\
                                 .find('ul').findAll('li')

        for group in groups:
            if group.text == group_name:
                return group['data-name']

        raise Exception("group '%s' not found" % group_name)

    def _parse_json(self, schedule_json):
        schedule = json.loads(schedule_json, encoding='utf-8')
        lessons = [TimeTableLessonEntry(l) for l in schedule['aSchedule'] if
                   l['type_entity'] == TimeTableLessonEntry.type_entity]

        with open(self.csv_filename, "w") as f:
            w = unicodecsv.writer(f, encoding='utf-8')

            w.writerow(GCalendarEntry.header_row)
            for lesson in lessons:
                start = time.localtime(lesson.start)
                end = time.localtime(lesson.end)

                start_date = time.strftime('%m/%d/%y', start)
                end_date = time.strftime('%m/%d/%y', end)

                start_time = time.strftime('%H:%M:%S', start)
                end_time = time.strftime('%H:%M:%S', end)

                description = "%s #%s. %s" % (lesson.type_title, str(lesson.number), lesson.lesson_title)
                location = unicode(lesson.auditorium_number)

                calendar_entry = GCalendarEntry(self.title_prefix + lesson.short_title,
                                                start_date, start_time, end_date, end_time, False,
                                                description, location, True)

                w.writerow(calendar_entry.to_tuple())


if __name__ == "__main__":
    OUTPUT_FILENAME = "out_tp.csv"
    GROUP_NAME = u"АПО-41"

    parser = TimetableParser(OUTPUT_FILENAME, GROUP_NAME)
    parser.parse()
