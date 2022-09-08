import os
import tempfile
from typing import Any, IO

from dotenv import load_dotenv  # type: ignore

import nox
from nox import Session

load_dotenv()

nox.options.sessions = "black", "lint", "tests"
locations = "src", "tests", "noxfile.py"


class CustomNamedTemporaryFile:
    """Alternative Temp file to allow compatibility with windows.

    This custom implementation is needed because of the following limitation of
    tempfile.NamedTemporaryFile:

    > Whether the name can be used to open the file a second time,
    while the named temporary file is still open,
    > varies across platforms (it can be so used on Unix;
     it cannot on Windows NT or later).
    """

    def __init__(self, mode: str = "wb", delete: bool = True) -> None:
        """Initiates CustomNamedTemporaryFile."""
        self._mode = mode
        self._delete = delete

    def __enter__(self) -> IO[Any]:
        """Creates and opens temp file."""
        # Generate a random temporary file name
        file_name = os.path.join(tempfile.gettempdir(), os.urandom(24).hex())
        self.filename = file_name
        # Ensure the file is created
        open(file_name, "x").close()
        # Open the file in the given mode
        self._tempFile = open(file_name, self._mode)
        return self._tempFile

    def __exit__(self, *args: tuple, **kwargs: dict) -> None:
        """Closes temp file."""
        self._tempFile.close()


def install_with_constraints(session: Session, *args: str, **kwargs: Any) -> None:
    """Install packages constrained by Poetry's lock file.
    This function is a wrapper for nox.sessions.Session.install. It
    invokes pip to install packages inside of the session's virtualenv.
    Additionally, pip is passed a constraints file generated from
    Poetry's lock file, to ensure that the packages are pinned to the
    versions specified in poetry.lock. This allows you to manage the
    packages as Poetry development dependencies.
    Arguments:
        session: The Session object.
        args: Command-line arguments for pip.
        kwargs: Additional keyword arguments for Session.install.
    """
    with CustomNamedTemporaryFile() as requirements:
        session.run(
            "poetry",
            "export",
            "--with=dev",
            "--format=requirements.txt",
            f"--output={requirements.name}",
            external=True,
        )
        session.install(f"--constraint={requirements.name}", *args, **kwargs)


@nox.session
def tests(session: Session) -> None:
    """Run the test suite."""
    args = session.posargs or ["--cov", "-m", "not e2e"]
    session.run("poetry", "install", "--no-dev", external=True)
    session.run("pytest", *args)


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
