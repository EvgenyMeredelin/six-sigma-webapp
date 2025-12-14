import inspect
import math
from functools import cached_property
from typing import Annotated, Literal, Self

import logfire
from environs import env
from fastapi import Depends, FastAPI, HTTPException, Path, status
from pydantic import (
    BaseModel, Field, computed_field,
    model_validator, NonNegativeInt,  PositiveInt
)
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from starlette.responses import RedirectResponse

from . import tools
from .settings import SigmaSupremum, MAX_P, SYSTEM_PROMPT


class SberProcess(BaseModel):
    """
    A process to evaluate with the "6 Sigma" approach.
    """

    tests: Annotated[PositiveInt, Field(
        description="The total number of tests.")]

    fails: Annotated[NonNegativeInt, Field(
        description="The number of tests qualified as failed.")]

    name: Annotated[str | None, Field(
        description="The name of the process (optional).")] = None

    @model_validator(mode="after")
    def prevent_fails_greater_than_tests(self) -> Self:
        if self.fails > self.tests:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "The number of fails can't be greater than the "
                    "total number of tests"
                )
            )
        return self

    @computed_field
    @cached_property
    def defect_rate(self) -> float:
        return self.fails / self.tests

    @computed_field
    @cached_property
    def sigma(self) -> float | str:
        # percent point function
        value = tools.norm.ppf(1 - self.defect_rate).item()
        # out of range float values are not JSON-compliant
        if math.isinf(value):
            return "-inf" if value < 0 else "inf"
        return value

    @computed_field
    @cached_property
    def label(self) -> str:
        # for sigma in {"-inf", "inf"}
        sigma = float(self.sigma)
        for sup in SigmaSupremum:
            if sigma < sup.value:
                return sup.name
        return sup.name


app = FastAPI(
    title="Six Sigma",
    description=(
        "Simple web app to evaluate a process "
        "with the \"6 Sigma\" approach"
    ),
    version="0.1.0",
    contact={
        "name": "Evgeny Meredelin",
        "email": "eimeredelin@sberbank.ru"
    }
)

logfire.instrument_fastapi(app)
logfire.instrument_pydantic_ai()

predicate = lambda obj: (
    inspect.isclass(obj)
    and obj is not tools.Handler
    and issubclass(obj, tools.Handler)
)

mode_handlers = {
    obj.mode: obj
    for _, obj in inspect.getmembers(tools)
    if predicate(obj)
}

Mode = Literal[tuple(mode_handlers)]


async def handle_request(
    mode: Mode,  # type: ignore
    process_list: list[SberProcess]
):
    handler_class = mode_handlers[mode]
    handler = handler_class(process_list)
    return await handler.handle_request()


agent = Agent(
    model=OpenAIChatModel(
        model_name=env("MODEL_NAME"),
        provider=OpenAIProvider()
    ),
    system_prompt=SYSTEM_PROMPT,
    output_type=SberProcess
)


@app.get("/")
async def redirect_from_root_to_docs():
    return RedirectResponse(url="/docs")


@app.get("/{mode}/prompt")
async def single_with_prompt(
    mode: Annotated[Mode, Path()],  # type: ignore
    prompt: str
):
    result = await agent.run(prompt)
    return await single(mode, result.output)


@app.get("/{mode}")
async def single(
    mode: Annotated[Mode, Path()],  # type: ignore
    process: Annotated[SberProcess, Depends()]
):
    return await handle_request(mode, [process])


@app.post("/{mode}")
async def bulk(
    mode: Annotated[Mode, Path()],  # type: ignore
    process_bulk: list[SberProcess]
):
    return await handle_request(mode, process_bulk[:MAX_P])
