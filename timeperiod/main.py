import re
from datetime import datetime, timedelta


NUMBERS = {
    'one': 1,
    'two': 2,
    'three': 3,
    'four': 4,
    'five': 5,
    'six': 6,
    'seven': 7,
    'eight': 8,
    'nine': 9,
    'ten': 10,
    'eleven': 11,
    'twelve': 12,
    'thirteen': 13,
    'fourteen': 14,
    'fifteen': 15,
    'sixteen': 16,
    'seventeen': 17,
    'eighteen': 18,
    'nineteen': 19,
    'twenty': 20,
    'thirty': 30,
    'forty': 40,
    'fifty': 50,
    'sixty': 60,
    'seventy': 70,
    'eighty': 80,
    'ninety': 90,
    'hundred': 100,
    'hundreds': 100,
    'thousand': 1000,
    'thousands': 1000,
    'million': 1000000,
    'millions': 1000000
}


PREDEFINED_PERIODS = {
    'yesterday': dict(direction='past', step='day', quantity=1),
    'today': dict(direction='current', step='day', quantity=0),
    'tomorrow': dict(direction='next', step='day', quantity=1)
}

_time_directions = {
    'current': ['current', 'this'],
    'future': ['next'],
    'past': ['last', 'past', 'previous'],
}

_time_periods = {
    'day': ['day', 'days'],
    'week': ['week', 'weeks'],
    'month': ['month', 'monthes'],
    'quarter': ['quarter', 'quarters'],
    'year': ['year', 'years']
}

def unfold_dicts(data):
    """
    transform the dict of lists to a dict:
    {a: [1, 11, 111], b: [2, 22]}
        >>
    {1: a, 11: a, 111: a, 2: b, 22: b}
    :param data:
    :return:
    """
    return {v: key for key, values in data.items() for v in values}


TIME_DIRECTIONS = unfold_dicts(_time_directions)
TIME_PERIODS = unfold_dicts(_time_periods)

DIRECTION_PATTERN = r"(\b{}\b)".format(r'\b|\b'.join(TIME_DIRECTIONS))
PERIOD_PATTERN = r"(\b{}\b)".format(r'\b|\b'.join(TIME_PERIODS))
QUANTITY_PATTERN = r'((\d+|\b{}\b)(\W|and|the|[a\.,])*)+'.format(r'\b|\b'.join(NUMBERS))


class DateParser:

    @classmethod
    def parse_period(cls, text, base_date=None):

        base_date = base_date or datetime.now()

        related_period = PREDEFINED_PERIODS.get(text)
        if not related_period:
            related_period, unused = cls.get_parsed_raw_data(text)

        if not related_period['direction'] or not related_period['step']:
            return None, None

        direction, quantity, step = cls.normalize_parsed_data(related_period)

        base_date = cls.get_base_date(base_date, step)

        if direction == 'future':
            dt_from = cls.increase_date(base_date, step)
            dt_to = cls.increase_date(dt_from, step, quantity)
        elif direction == 'past':
            dt_to = base_date
            dt_from = cls.decrease_date(dt_to, step, quantity)
        else:
            dt_from = base_date
            dt_to = cls.increase_date(dt_from, step)
        return dt_from, dt_to

    @classmethod
    def get_parsed_token(cls, pattern, text):
        z = re.search(pattern, text)
        if not z:
            return '', text

        text = f'{text[:z.start()].strip()} {text[z.end():].strip()}'
        return z.group().strip(), text.strip()

    @classmethod
    def get_parsed_direction(cls, text):
        period, _ = cls.get_parsed_token('the\W+' + PERIOD_PATTERN, text)
        if period.startswith('the '):
            return 'current', text

        return cls.get_parsed_token(DIRECTION_PATTERN, text)

    @classmethod
    def get_parsed_quantity(cls, text):
        return cls.get_parsed_token(QUANTITY_PATTERN, text)

    @classmethod
    def get_parsed_step(cls, text):
        return cls.get_parsed_token(PERIOD_PATTERN, text)

    @classmethod
    def get_parsed_raw_data(cls, text):
        direction, text = cls.get_parsed_direction(text)
        quantity, text = cls.get_parsed_quantity(text)
        step, text = cls.get_parsed_step(text)
        return dict(direction=direction, quantity=quantity, step=step), text

    @classmethod
    def parse_numeric_words(cls, text):
        grades = {}
        result = 0
        for w in text.split():
            if not w:
                continue
            if re.fullmatch('\d+', w):
                result += int(w)
            number = NUMBERS.get(w, 0)
            if number in [100, 1000, 1000000] and result:
                grades[number] = grades.get(number, 0) + result * number
                result = 0
            else:
                result += number
        return result + sum(grades.values())

    @classmethod
    def normalize_parsed_data(cls, data):
        """
        Reduces time_direction to current / future / past value
        + convert quantity yo int.

        :param data:
            dict(direction, quantity, period)
        :return:
        """
        return (TIME_DIRECTIONS[data.get('direction') or 'past'],
                int(data.get('quantity') or 1),
                TIME_PERIODS[data.get('step') or 'day'])

    @classmethod
    def get_base_date(cls, basedate, step):
        base_date = basedate.replace(microsecond=0, second=0, minute=0, hour=0)
        if step == 'week':
            base_date -= timedelta(days=base_date.weekday())
        elif step == 'month':
            base_date = add_month(base_date, 0)
        elif step == 'quarter':
            base_date = quarter_start(base_date)
        elif step == 'year':
            base_date = base_date.replace(day=1, month=1)
        return base_date

    @classmethod
    def increase_date(cls, basedate, step, quantity=1):
        result = None
        if step == 'day':
            result = basedate + timedelta(days=quantity)
        elif step == 'week':
            result = basedate + timedelta(days=quantity * 7)
        elif step == 'month':
            result = add_month(basedate, quantity)
        elif step == 'quarter':
            result = add_month(basedate, quantity * 3)
        elif step == 'year':
            result = basedate.replace(year=basedate.year + quantity)
        return result

    @classmethod
    def decrease_date(cls, basedate, step, quantity=1):
        return cls.increase_date(basedate, step, -quantity)


def add_month(dt, m):
    y, m = divmod(dt.month + m, 12)
    if m == 0:
        y, m = y - 1, 12
    return dt.replace(day=1, year=dt.year + y, month=m)


def quarter_start(dt):
    return add_month(dt, -((dt.month - 1) % 3))
