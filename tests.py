"""
Should parse simple cases like

today
yesterday
tomorrow
last week / month / quarter / year
last X weeks / months / quarters / years

next X ...

"""
from datetime import datetime

import pytest

from timeperiod import DateParser, quarter_start
from timeperiod.main import QUANTITY_PATTERN


@pytest.mark.parametrize('text, dt_from, dt_to', [
    ('yesterday', datetime(2018, 10, 9, 0, 0, 0), datetime(2018, 10, 10, 0, 0, 0)),
    ('today', datetime(2018, 10, 10, 0, 0, 0), datetime(2018, 10, 11, 0, 0, 0)),
    ('tomorrow', datetime(2018, 10, 11, 0, 0, 0), datetime(2018, 10, 12, 0, 0, 0)),
])
def test_predefined(text, dt_from, dt_to):
    base_date = datetime(2018, 10, 10, 9, 30, 00)
    _from, _to = DateParser().parse_period(text, base_date)
    assert _from == dt_from
    assert _to == dt_to


@pytest.mark.parametrize('text', [
    'unknown words', 'next song', '7 cars', 'every week'
])
def test_unknown(text):
    assert (None, None) == DateParser().parse_period(text)


@pytest.mark.parametrize('text, _from, _to', [
    ('the year', datetime(2018, 1, 1, 0, 0, 0), datetime(2019, 1, 1, 0, 0, 0)),
    ('the next year', datetime(2019, 1, 1, 0, 0, 0), datetime(2020, 1, 1, 0, 0, 0)),
    ('the last year', datetime(2017, 1, 1, 0, 0, 0), datetime(2018, 1, 1, 0, 0, 0)),
    ('last forty three days', datetime(2018, 8, 28, 0, 0, 0), datetime(2018, 10, 10, 0, 0, 0)),
    ('next eleven weeks', datetime(2018, 10, 15, 0, 0),  datetime(2018, 12, 31, 0, 0)),
    ('the longest year', None, None),
])
def test_the_period(text, _from, _to):
    base_date = datetime(2018, 10, 10, 9, 30, 00)
    assert DateParser().parse_period(text, base_date) == (_from, _to)


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


@pytest.mark.parametrize('text, parsed, unused', [
    ('last 2 weeks', ('last', '2', 'weeks'), ''),
    ('next month', ('next', '', 'month'), ''),
    ('previous 2 quarters', ('previous', '2', 'quarters'), ''),
    ('last 5 long years', ('last', '5', 'years'), 'long'),
    ('past year', ('past', '', 'year'), ''),
    ('', ('', '', ''), ''),
])
def test_get_parsed_data(text, parsed, unused):
    data, parsed_unused = DateParser().get_parsed_raw_data(text)
    assert data == dict(zip(['direction', 'quantity', 'step'], parsed))
    assert parsed_unused == unused


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
    ('last 123.4 weeks', '123.4', 'last weeks'),
])
def test_quantity_pattern(text, quantity, subtext):
    assert (quantity, subtext) == DateParser().get_parsed_quantity(text)


@pytest.mark.parametrize('text, period, subtext', [
    ('last 2 dayz', '', 'last 2 dayz'),
    ('last 2 dday', '', 'last 2 dday'),
    ('last 2 weeks', 'weeks', 'last 2'),
    ('last 2 weeksss', '', 'last 2 weeksss'),
    ('the next month', 'month', 'the next'),
    ('the next 3 months', 'months', 'the next 3'),
    ('2 weeks ago', 'weeks', '2 ago'),
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


@pytest.mark.parametrize('text, result', [
    ('one', ('one', '')),
    ('  two  ', ('two', '')),
    (' forty  two', ('forty  two', '')),
    ('two thousands and three hundreds twenty four',
     ('two thousands and three hundreds twenty four', '')),
    ('two thousands and three fail hundreds twenty four',
     ('two thousands and three', 'fail hundreds twenty four')),
])
def test_parse_word_numbers(text, result):
    print(text, result)
    assert DateParser.get_parsed_token(QUANTITY_PATTERN, text) == result




@pytest.mark.parametrize('text, result', [
    ('one', 1),
    ('one and three', 4),
    ('  two  ', 2),
    (' forty two', 42),
    ('two thousands and three hundreds twenty four', 2324),
    ('two thousands and thousands', 3000),
    ('two thousands and 247', 2247),
])
def test_parse_numbers(text, result):
    assert DateParser.parse_numeric_words(text) == result
