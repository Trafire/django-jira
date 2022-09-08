from dotenv import load_dotenv  # type: ignore

import nox
from nox import Session

load_dotenv()

nox.options.sessions = "black", "lint", "mypy", "tests"
locations = "src", "tests", "noxfile.py"


@nox.session
def tests(session: Session) -> None:
    session.run("pytest")


# noxfile.py
@nox.session(python="3.8", reuse_venv=True)
def black(session: Session) -> None:
    """Run black code formatter."""
    args = session.posargs or locations
    session.install("black")
    session.run("black", *args)


@nox.session(python="3.8")
def lint(session: Session) -> None:
    args = session.posargs or locations
    session.install(
        "flake8",
        "flake8-bandit",
        "flake8-black",
        "flake8-bugbear",
        "flake8-import-order",
    )
    session.run("flake8", *args)


@nox.session(python=["3.8"])
def mypy(session: Session) -> None:
    args = session.posargs or locations
    session.install("mypy")
    session.run("mypy", *args)
