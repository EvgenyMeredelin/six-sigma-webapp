## Simple web app to evaluate a process with the "6 Sigma" approach

* `/data` — data-only mode: process(es) enriched with computed fields;
* `/plot` — plot as binary content and data in the "Process-List" header (examples below);
* `/obs` — plot and data uploaded to a bucket

```python
import io
import json

import requests
from PIL import Image


url = "http://localhost:1703/plot"

params = {
    "tests": 1500,
    "fails": 256,
    "name": "Example process"
}

r = requests.get(url, params=params)
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

r = requests.post(url, data=json.dumps(data))
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
