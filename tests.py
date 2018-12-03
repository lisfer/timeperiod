"""
Should parse simple cases like

today
yesterday
tomorrow
last week / month / quarter / year
last X weeks / monthes / quarters / years

next X ...

"""
from datetime import datetime

import pytest

from main import DateParser, quarter_start


def test_yesterday():
    base_date = datetime(2018, 10, 10, 9, 30, 00)
    data = DateParser().parse_period('yesterday', base_date)
    assert data['from'] == datetime(2018, 10, 9, 0, 0, 0)
    assert data['to'] == datetime(2018, 10, 10, 0, 0, 0)


def test_related_period():
    data = DateParser().parse_period('yesterday')
    assert data['period'] == 'day'
    assert data['quantity'] == 1
    assert data['direction'] == 'past'


def test_last_week():
    base_date = datetime(2018, 10, 17, 9, 30, 00)
    dt_from, dt_to = DateParser().parse_period('last week', base_date)
    assert dt_from == datetime(2018, 10, 8, 0, 0, 0)
    assert dt_to == datetime(2018, 10, 15, 0, 0, 0)


def test_last_two_week():
    base_date = datetime(2018, 10, 17, 9, 30, 00)
    dt_from, dt_to = DateParser().parse_period('last 2 weeks', base_date)
    assert dt_from == datetime(2018, 10, 1, 0, 0, 0)
    assert dt_to == datetime(2018, 10, 15, 0, 0, 0)


@pytest.mark.parametrize('text, parsed', [
    ('last 2 weeks', ('last', '2', 'week', '')),
    ('next month', ('next', '', 'month', '')),
    ('previous 2 quarters', ('previous', '2', 'quarter', '')),
    ('last 5 long years', ('last', '5', 'year', 'long')),
    ('past years', ('past', '', 'year', '')),
    ('', ('', '', '', '')),
])
def test_get_parsed_data(text, parsed):
    data = DateParser().get_parsed_raw_data(text)
    assert data == dict(zip(['direction', 'quantity', 'step', 'unused'], parsed))


@pytest.mark.parametrize('text, direction, subtext', [
    ('last 2 weeks', 'last', '2 weeks'),
    ('lastt 2 weeks', '', 'lastt 2 weeks'),
    ('llast 2 weeks', '', 'llast 2 weeks'),
    ('the next month', 'next', 'the month'),
    ('2 weeks', '', '2 weeks'),
    ('', '', ''),
    ('this', 'this', ''),
])
def test_direction_pattern(text, direction, subtext):
    assert (direction, subtext) == DateParser().get_parsed_direction(text)


@pytest.mark.parametrize('text, quantity, subtext', [
    ('last 2 weeks', '2', 'last weeks'),
    ('the next month', '', 'the next month'),
    ('2 weeks', '2', 'weeks'),
    ('22', '22', ''),
    ('', '', ''),
    ('last 123.4 weeks', '123', 'last .4 weeks'),
])
def test_quantity_pattern(text, quantity, subtext):
    assert (quantity, subtext) == DateParser().get_parsed_quantity(text)


@pytest.mark.parametrize('text, period, subtext', [
    ('last 2 dayz', '', 'last 2 dayz'),
    ('last 2 dday', '', 'last 2 dday'),
    ('last 2 weeks', 'week', 'last 2'),
    ('last 2 weeksss', '', 'last 2 weeksss'),
    ('the next month', 'month', 'the next'),
    ('the next 3 monthes', 'month', 'the next 3'),
    ('2 weeks ago', 'week', '2 ago'),
    ('yesterday', '', 'yesterday'),
    ('week', 'week', ''),
    ('', '', ''),
])
def test_step_pattern(text, period, subtext):
    assert (period, subtext) == DateParser().get_parsed_step(text)


@pytest.mark.parametrize('income, outcome', [
    (('', '', '', ''), ('past', 1, 'day')),
    (('last', '2', 'week', ''), ('past', 2, 'week')),
    (('next', '3', 'month', ''), ('future', 3, 'month')),
    (('past', '11', 'month', ''), ('past', 11, 'month')),
    (('current', '', 'quarter', ''), ('current', 1, 'quarter')),
])
def test_normalize_parsed_data(income, outcome):
    income = dict(zip(['direction', 'quantity', 'step', 'unused'], income))
    assert DateParser.normalize_parsed_data(income) == outcome


@pytest.mark.parametrize('basedate, period, outcome', [
    (datetime(2018, 10, 10, 14, 14, 41), 'day', datetime(2018, 10, 10, 0, 0, 0)),

    (datetime(2018, 10, 10, 14, 14, 41), 'week', datetime(2018, 10, 8, 0, 0, 0)),
    (datetime(2018, 11, 4, 14, 14, 41), 'week', datetime(2018, 10, 29, 0, 0, 0)),
    (datetime(2018, 11, 5, 14, 14, 41), 'week', datetime(2018, 11, 5, 0, 0, 0)),
    (datetime(2019, 1, 2, 14, 14, 41), 'week', datetime(2018, 12, 31, 0, 0, 0)),

    (datetime(2018, 10, 10, 14, 14, 41), 'month', datetime(2018, 10, 1, 0, 0, 0)),

    (datetime(2018, 10, 10, 14, 14, 41), 'quarter', datetime(2018, 10, 1, 0, 0, 0)),
    (datetime(2018, 9, 10, 14, 14, 41), 'quarter', datetime(2018, 7, 1, 0, 0, 0)),

    (datetime(2018, 9, 10, 14, 14, 41), 'year', datetime(2018, 1, 1, 0, 0, 0))
])
def test_base_date(basedate, period, outcome):
    assert DateParser.get_base_date(basedate, period) == outcome


@pytest.mark.parametrize('month_in, month_out', [
    (1, 1), (2, 1), (3, 1), (4, 4), (5, 4), (6, 4),
    (7, 7), (8, 7), (9, 7), (10, 10), (11, 10), (12, 10)
])
def test_quarter_start(month_in, month_out):
    dt_in = datetime(2018, 10, 10, 13, 13, 13).replace(month=month_in)
    assert quarter_start(dt_in).month == month_out


@pytest.mark.parametrize('dt, step, quantity, result', [
    (datetime(2018, 10, 10, 14, 14, 41), 'day', 2, datetime(2018, 10, 12, 14, 14, 41)),
    (datetime(2018, 10, 31, 14, 14, 41), 'day', 2, datetime(2018, 11, 2, 14, 14, 41)),
    (datetime(2018, 10, 14, 14, 14, 41), 'week', 2, datetime(2018, 10, 28, 14, 14, 41)),
    (datetime(2018, 10, 30, 14, 14, 41), 'month', 1, datetime(2018, 11, 1, 14, 14, 41)),
    (datetime(2018, 10, 30, 14, 14, 41), 'month', 3, datetime(2019, 1, 1, 14, 14, 41)),
    (datetime(2018, 10, 10, 14, 14, 41), 'year', 2, datetime(2020, 10, 10, 14, 14, 41)),

])
def test_increase_date(dt, step, quantity, result):
    assert DateParser.increase_date(dt, step, quantity) == result


@pytest.mark.parametrize('dt, step, quantity, result', [
    (datetime(2018, 10, 10, 14, 14, 41), 'day', 2, datetime(2018, 10, 8, 14, 14, 41)),
    (datetime(2018, 11, 1, 14, 14, 41), 'day', 2, datetime(2018, 10, 30, 14, 14, 41)),
    (datetime(2018, 10, 14, 14, 14, 41), 'week', 2, datetime(2018, 9, 30, 14, 14, 41)),
    (datetime(2018, 10, 30, 14, 14, 41), 'month', 1, datetime(2018, 9, 1, 14, 14, 41)),
    (datetime(2019, 1, 30, 14, 14, 41), 'month', 3, datetime(2018, 10, 1, 14, 14, 41)),
    (datetime(2018, 10, 10, 14, 14, 41), 'year', 2, datetime(2016, 10, 10, 14, 14, 41)),

])
def test_decrease_date(dt, step, quantity, result):
    assert DateParser.decrease_date(dt, step, quantity) == result
