import io
import json
import math
import operator
from abc import ABC, abstractmethod
from dataclasses import dataclass
from types import NoneType
from uuid import uuid4

import boto3
import matplotlib.pyplot as plt
import mplcyberpunk
import numpy as np
from botocore.client import Config
from environs import env
from fastapi import Response
from matplotlib.ticker import FormatStrFormatter
from scipy import stats

from .settings import (
    DPI_SINGLE, DPI_BULK, MPL_RUNTIME_CONFIG,
    NAME_DISPLAY_LIMIT, LOC
)


# Normal continuous random variable with loc=LOC and scale=1 (default).
# https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html
norm = stats.norm(LOC)


class Handler(ABC):
    """Abstract base handler. """

    def __init__(self, process_list):
        self.process_list = process_list

    @property
    @abstractmethod
    def mode(self):
        raise NotImplementedError

    @abstractmethod
    def handle_request(self):
        raise NotImplementedError


class Slacker(Handler):
    """A do-nothing handler. """

    mode = "data"

    def handle_request(self):
        return self.process_list


class Plotter(Handler):
    """A handler capable of plotting the sigma of a process. """

    mode = "plot"

    def __init__(self, process_list):
        super().__init__(process_list)
        self.buffer = io.BytesIO()
        self.dumps = []
        self._plot_sigma()

    def _plot_sigma(self):
        # Select Anti-Grain Geometry backend to prevent warning "Starting a
        # Matplotlib GUI outside of the main thread will likely fail".
        # https://matplotlib.org/stable/users/explain/figure/backends.html
        plt.rcParams.update(MPL_RUNTIME_CONFIG)
        plt.style.use("cyberpunk")
        plt.switch_backend("agg")

        nrows = len(self.process_list)
        fig, ax = plt.subplots(
            nrows=nrows, figsize=(8, 2.2*nrows), squeeze=False,
            dpi=DPI_SINGLE if nrows == 1 else DPI_BULK
        )
        plt.subplots_adjust(hspace=0.5)
        ax_iter = ax.flat

        xmin, xmax = -3, 6
        x = np.linspace(xmin, xmax, 100*(xmax - xmin) + 1)
        y = norm.pdf(x)  # probability density function
        xticks = list(range(xmin, xmax + 1)) + [LOC]

        for process in self.process_list:
            dump = process.model_dump()
            self.dumps.append(dump)
            tests, fails, name, defect_rate, sigma, label = dump.values()
            sigma = float(sigma)  # for sigma in {"-inf", "inf"}
            sigma_clipped = np.clip(sigma, xmin, xmax)
            xfill = np.linspace(sigma_clipped, xmax)

            dr_label = f"Defect rate = {defect_rate * 100:.2f}%"
            aes = {"label": dr_label, "color": label.lower(), "alpha": 0.44}
            norm_label = f"$N(\\mu = {LOC}, \\sigma = 1)$"
            sigma_annotation = f"$\\sigma$ = {sigma:.3f}"
            name = f", name={name[:NAME_DISPLAY_LIMIT]!r}" if name else ""
            title = f"{process.__class__.__name__}({tests=}, {fails=}{name})"

            ax = next(ax_iter)
            ax.plot(x, y, lw=1.2, label=norm_label)
            ax.fill_between(xfill, norm.pdf(xfill), 0, **aes)
            ax.annotate(sigma_annotation, size=15, xy=(0.84, 0.2))
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(0, y.max() + 0.03)
            ax.set_xticks(xticks)
            ax.tick_params(axis="both", labelsize=8)
            ax.xaxis.set_major_formatter(FormatStrFormatter("%.2g"))
            ax.grid(lw=0.6)
            ax.legend(frameon=True, framealpha=1, loc="upper left")
            ax.set_title(title)

            mplcyberpunk.make_lines_glow(ax=ax)
            mplcyberpunk.add_underglow(ax=ax)

        plt.savefig(self.buffer, bbox_inches="tight", format="png")
        self.buffer.seek(0)
        plt.close(fig)

    def handle_request(self):
        return Response(
            content=self.buffer.getvalue(),
            headers={
                "Content-Disposition": "inline; filename=plot.png",
                "Process-List": json.dumps(self.dumps)
            },
            media_type="image/png"
        )


class Uploader(Plotter):
    """A plotter capable of uploading a plot and data to a bucket. """

    mode = "obs"

    def handle_request(self):
        session = boto3.session.Session(
            aws_access_key_id=env("KEY_ID"),
            aws_secret_access_key=env("KEY_SECRET"),
            region_name=env("REGION")
        )
        client = session.client(
            service_name="s3",
            endpoint_url=env("ENDPOINT"),
            config=Config(s3={"addressing_style": "virtual"})
        )

        folder = str(uuid4())
        bucket = env("BUCKET")

        client.put_object(
            Bucket=bucket,
            Key=f"{folder}/plot.png",
            Body=self.buffer,
            ContentType="image/png"
        )
        client.put_object(
            Bucket=bucket,
            Key=f"{folder}/process_list.json",
            Body=json.dumps(self.dumps, indent=4).encode("utf-8"),
            ContentType="application/json"
        )

        return {
            "bucket": bucket,
            "folder": folder,
            "process_list": self.dumps,
        }


class EqMixin:
    """Mixin that implements a field type aware equality test. """

    testers = {
        str: operator.eq,
        int: operator.eq,
        NoneType: operator.eq,
        float: math.isclose
    }

    def __eq__(self, other) -> bool:
        if isinstance(other, self.__class__):
            return all(
                self.__class__.testers[type(v)](v, other.__dict__[k])
                for k, v in self.__dict__.items()
            )
        return NotImplemented


@dataclass(eq=False)
class ComparableDump(EqMixin):
    """A SberProcess dump with a field type aware equality test. """

    tests: int
    fails: int
    defect_rate: float
    sigma: float
    label: str
    name: str | None = None
