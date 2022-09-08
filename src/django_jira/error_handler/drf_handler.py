"""Exception Handler for DRF sending bug reports to Jira."""
import datetime
import os
import sys
from typing import Iterable, Optional

from jinja2 import (  # type: ignore
    Environment,
    FileSystemLoader,
)

from rest_framework.request import Request  # type: ignore
from rest_framework.views import exception_handler  # type: ignore

from django_jira.tasks.tasks import Attachment, create_connection  # type: ignore


def get_attachments(files: Iterable):
    """
    It takes a list of files and returns a list of attachments

    Args:
      files: A list of files to attach to the email.

    Returns:
      A list of Attachment objects.
    """
    return [Attachment(filename=f.name, data=f) for f in files]


def trace_error(exc: Exception):
    """Get Information on error.

    It takes an exception, and returns a dictionary with the exception's type,
    message, traceback, and any files attached to
    the request

    Args:
      exc (Exception): The exception that was raised.

    Returns:
      A dictionary with the type of error, the message,
        the trace, and the attachments.
    """
    trace = []
    tb = exc.__traceback__
    files: set = set()
    while tb is not None:
        locals = tb.tb_frame.f_locals
        request: Optional[Request] = locals.get("request")
        try:
            username: str = request.user.username  # type: ignore
        except AttributeError:
            username = ""
        try:
            for _, value in request.FILES.items():  # type: ignore
                files.add(value)
        except AttributeError:
            pass

        f_code = tb.tb_frame.f_code
        trace.append(
            {
                "filename": f_code.co_filename,
                "name": f_code.co_name,
                "lineno": tb.tb_lineno,
                "locals": locals,
                "request": request,
                "username": username,
            }
        )
        tb = tb.tb_next

    return {
        "type": type(exc).__name__,
        "message": str(exc),
        "trace": trace,
        "attachments": get_attachments(files),
    }


def error_title(trace: dict):
    """Title for Issue in Jira.
    It takes a traceback dictionary and returns a string
        that is the title of the error.

    Args:
      trace (dict): The traceback object.

    Returns:
      A string with the title of the project, the type of error,
      the error message, the filename, and the line number.
    """
    return (
        f'{os.environ.get("PROJECT_NAME", "Unknown Project").title()} '
        f'{trace["type"]}: '
        f'{trace["message"].title()} in '
        f'{trace["trace"][-1]["filename"]} at line '
        f'{trace["trace"][-1]["lineno"]}'.replace("\\", "/")
    )


def drf_jira_exception_handler(exc: Exception, context: dict):
    """Custom Exception Handler creates Jira Bug Reports.

    Returns the same as
    creates a JIRA bug report, and returns a response to the user

    Args:
      exc (Exception): The exception instance raised.
      context (dict): The context parameter is a
        dictionary that contains the following keys:


    Returns:
      The response is being returned.
    """
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    if response is None or response.status_code >= 500:
        template_path = (
            os.path.dirname(
                str(sys.modules[drf_jira_exception_handler.__module__].__file__)
            )
            + "/templates"
        )
        environment = Environment(
            loader=FileSystemLoader(searchpath=template_path), autoescape=True
        )
        template = environment.get_template("drf_error_template.md")
        trace = trace_error(exc)

        content = template.render(
            exc=exc,
            context=context,
            exc_name=error_title(trace),
            request=context["request"],
            parameters=zip(
                context["request"].query_params.keys(),
                context["request"].query_params.values(),
            ),
            time=datetime.datetime.now(),
            stacktrace=trace["trace"],
        )
        # content = str(trace_error(exc))
        jira = create_connection()
        jira.create_bug_report(error_title(trace), content, trace["attachments"])

    return response
