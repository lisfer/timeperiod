import re
from datetime import datetime, timedelta


PREDEFINED_PERIODS = {
    'yesterday': dict(direction='past', step='day', quantity=1),
    'today': dict(direction='current', step='day', quantity=0),
    'tomorrow': dict(direction='next', step='day', quantity=1)
}

TIME_DIRECTIONS = {
    'current': 'current',
    'this': 'current',
    'next': 'future',
    'last': 'past',
    'past': 'past',
    'previous': 'past',
}

TIME_PERIODS = {
    'day': 's',
    'week': 's',
    'quarter': 's',
    'month': 'es',
    'year': 's'
}

DIRECTION_PATTERN = r"(\b{}\b)".format(r'\b|\b'.join(TIME_DIRECTIONS))
QUANTITY_PATTERN = rf"(?P<quantity>\d+)"

#\b(?P<period>day(?=({s})?\b)|...|year(?=(s)?\b)))
PERIOD_PATTERN =  r"\b(?P<period>{})".format(
    '|'.join([rf'{k}(?=({v})?\b)' for k, v in TIME_PERIODS.items()]))


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
        for start, end in z.regs[-1:0:-1]:
            if text and (start, end) != (-1, -1):
                text = f'{text[:start].strip()} {text[end:].strip()}'
        return z.group(), text.strip()

    @classmethod
    def get_parsed_direction(cls, text):
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
                data.get('step') or 'day')

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
