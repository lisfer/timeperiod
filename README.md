# timeperiod
A simple parser of time periods specified in a text to datetime objects.

## Installation:
```bash
pip install git+https://github.com/lisfer/timeperiod.git
```

Lib parser phrases like "**&lt;time_direction&gt** [**&lt;number&gt;**] **&lt;time_period&gt**" where

**&lt;time_direction&gt** - one of the next values: *last / past / previous / current / this / next*

**&lt;number&gt;** - number of "periods". Can be absent

**&lt;time_period&gt;** - one of the next values *day(s) / week(s) / month(es) / quarter(s) / year(s)*

## Usage

```python
from timeperiod import DateParser
from datetime import datetime

z = datetime(2018, 10, 10, 13, 15, 16)

DateParser.parse_period('last 3 weeks', z)
>>> (datetime.datetime(2018, 9, 17, 0, 0), datetime.datetime(2018, 10, 8, 0, 0))

DateParser.parse_period('next month', z)
>>> (datetime.datetime(2018, 11, 1, 0, 0), datetime.datetime(2018, 12, 1, 0, 0))

DateParser.parse_period('last quarter', z)
>>> (datetime.datetime(2018, 7, 1, 0, 0), datetime.datetime(2018, 10, 1, 0, 0))

DateParser.parse_period('today', z)
>>> (datetime.datetime(2018, 10, 10, 0, 0), datetime.datetime(2018, 10, 11, 0, 0))

DateParser.parse_period('tomorrow', z)
>>> (datetime.datetime(2018, 10, 11, 0, 0), datetime.datetime(2018, 10, 12, 0, 0))

