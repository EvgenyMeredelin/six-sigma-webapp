import logfire
import uvicorn
from environs import env
env.read_env()


logfire.configure(
    token=env("LOGFIRE_SIXSIGMA"),
    code_source=logfire.CodeSource(
        repository="https://github.com/EvgenyMeredelin/six-sigma-webapp",
        revision="main"
    )
)
logfire.install_auto_tracing(modules=["app"], min_duration=0)
logfire.instrument_pydantic_ai()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=env("ECS_PRIVATE_IP"),
        port=env.int("ECS_PORT")
    )
