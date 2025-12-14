## Simple web app to evaluate a process with the "6 Sigma" approach

`GET` for a single process, `POST` for a list of processes:

* `GET/POST /data` — data-only mode: process(es) enriched with computed fields;
* `GET/POST /plot` — plot as binary content and data in the "Process-List" header (examples below);
* `GET/POST /obs` — plot and data uploaded to a bucket;
* `GET {mode}/prompt` — `data`/`plot`/`obs` mode with a prompt for a single process.


### `GET /plot`

```python
import io
import json

import requests
from PIL import Image


r = requests.get(
    url="http://localhost:1703/plot",
    params={
        "tests": 1500,
        "fails": 256,
        "name": "Example process"
    }
)
Image.open(io.BytesIO(r.content))
```

![six-sigma-single-plot](https://github-assets.s3-website.cloud.ru/six-sigma/single.png)

```python
json.loads(r.headers["Process-List"])
```

```
[
    {
        "tests": 1500,
        "fails": 256,
        "name": "Example process",
        "defect_rate": 0.17066666666666666,
        "sigma": 2.4515340671620525,
        "label": "YELLOW"
    }
]
```


### `POST /plot`

```python
data = [
    {
        "tests": 1e6,
        "fails": 274254,
        "name" : "Red class..."
    },
    {
        "tests": 1e6,
        "fails": 274253,
        "name" : "...turned Yellow"
    },
    {
        "tests": 1e6,
        "fails": 4662,
        "name" : "...is still Yellow"
    },
    {
        "tests": 1e6,
        "fails": 4661,
        "name" : "...and now it's Green"
    }
]

r = requests.post(
    url="http://localhost:1703/plot",
    data=json.dumps(data)
)
Image.open(io.BytesIO(r.content))
```

![six-sigma-bulk-plot](https://github-assets.s3-website.cloud.ru/six-sigma/bulk.png)

```python
json.loads(r.headers["Process-List"])
```

```
[
    {
        "tests": 1000000,
        "fails": 274254,
        "name": "Red class...",
        "defect_rate": 0.274254,
        "sigma": 2.0999973523886952,
        "label": "RED"
    },
    {
        "tests": 1000000,
        "fails": 274253,
        "name": "...turned Yellow",
        "defect_rate": 0.274253,
        "sigma": 2.1000003533655227,
        "label": "YELLOW"
    },
    {
        "tests": 1000000,
        "fails": 4662,
        "name": "...is still Yellow",
        "defect_rate": 0.004662,
        "sigma": 4.099940225647758,
        "label": "YELLOW"
    },
    {
        "tests": 1000000,
        "fails": 4661,
        "name": "...and now it's Green",
        "defect_rate": 0.004661,
        "sigma": 4.10001384285712,
        "label": "GREEN"
    }
]
```


### `GET /obs/prompt`

```python
r = requests.get(
    url="http://localhost:1703/obs/prompt",
    params={"prompt": "265 хороших деталей и 17 бракованных"}
)
r.json()
```

```
{
    'bucket': 'oait-bucket',
    'folder': 'e0e9ff8f-867c-4af2-af19-8ccf5bb16d45',
    'process_list': [
        {
            'tests': 282,
            'fails': 17,
            'name': None,
            'defect_rate': 0.06028368794326241,
            'sigma': 3.0523965189119027,
            'label': 'YELLOW'
        }
    ]
}
```


### Pytest & coverage

```
$ pytest --cov-report term-missing --cov-report html:htmlcov --cov=. -vv
=================================== test session starts ====================================
platform win32 -- Python 3.13.7, pytest-8.3.5, pluggy-1.5.0 -- D:\git\six-sigma-webapp\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\git\six-sigma-webapp
configfile: pytest.ini
plugins: anyio-4.9.0, logfire-3.19.0, cov-6.0.0
collected 10 items

app/test_main.py::test_no_tests_performed PASSED                                      [ 10%]
app/test_main.py::test_negative_tests_negative_fails PASSED                           [ 20%]
app/test_main.py::test_fails_greater_than_tests PASSED                                [ 30%]
app/test_main.py::test_string_tests_string_fails PASSED                               [ 40%]
app/test_main.py::test_float_coercible_to_integer PASSED                              [ 50%]
app/test_main.py::test_fails_equals_tests PASSED                                      [ 60%]
app/test_main.py::test_no_tests_failed PASSED                                         [ 70%]
app/test_main.py::test_fails_thresholds_for_one_million_tests PASSED                  [ 80%]
app/test_main.py::test_single_with_prompt PASSED                                      [ 90%]
app/test_main.py::test_redirect_to_docs PASSED                                        [100%]

---------- coverage: platform win32, python 3.13.7-final-0 -----------
Name                      Stmts   Miss  Cover   Missing
-------------------------------------------------------
app\__init__.py               0      0   100%
app\botocore_client.py       17      0   100%
app\main.py                  65      0   100%
app\settings.py              12      0   100%
app\test_main.py             74      0   100%
app\tools.py                106      4    96%   39, 43, 52, 179
logfire_auto_tracing.py       9      9     0%   1-18
-------------------------------------------------------
TOTAL                       283     13    95%
Coverage HTML written to dir htmlcov


=================================== 10 passed in 11.72s ====================================
```