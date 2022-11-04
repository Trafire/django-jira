# Importing the JIRA class from the jira module.
import io
import os
from typing import Any, Dict, List, Optional, Tuple, Union

from jira import JIRA  # type: ignore
from jira.client import ResultList  # type: ignore
from jira.resources import Board, Issue  # type: ignore

from pydantic import BaseModel


class Attachment(BaseModel):
    filename: str = ""
    data: Any = io.BytesIO(b"")
    filepath: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


# This class is a wrapper for the JIRA class in the jira module.
# It adds a few methods to the JIRA class to make it easier
# make it more specialized for the ERP project
class JiraTask(JIRA):
    def __init__(
        self,
        server: str,
        email: str,
        token: str,
        board_name,
        project_key,
        final_stage="Done",
        **kwargs: dict,
    ):
        """The function __init__ is a constructor that takes three parameters.

        Args:
          server (str): The URL of your Jira instance.
          email (str): Email address associated with token.
          token (str): The API token for jira.
          kwargs(dict): Other options defined in JIRA object.
        """
        super(JiraTask, self).__init__(server=server, basic_auth=(email, token))
        self.board_name = board_name
        self.project_key = project_key
        # Used to know whether we should create a new bug report
        self.final_stage = final_stage

    def boards(self, **kwargs) -> ResultList[Board]:
        kwargs["name"] = self.board_name
        """Get a list of board resources.
        Name will be overidden by self.board_name

        Args:
            startAt: The starting index of the returned boards.
                Base index: 0.
            maxResults: The maximum number of boards to return per page.
                Default: 50
            type: Filters results to boards of the specified type.
                Valid values: scrum, kanban.
            name: Filters results to boards that match or partially
                match the specified name.
            projectKeyOrID: Filters results to boards that match
                the specified project key or ID.

        Returns:
            ResultList[Board]
        """
        return super(JiraTask, self).boards(**kwargs)

    @property
    def board_id(self) -> int:
        """
        It returns the id of the first board in the list of boards.

        Returns:
          The id of the first board in the list of boards.
        """
        return self.boards()[0].id

    @property
    def project_id(self) -> int:
        return self.project(self.project_key).id

    def search_issues(
        self, jql_str: str = "", page: int = 1, **kwargs: dict
    ) -> Union[Dict[str, Any], ResultList[Issue]]:
        """
        It searches for issues in Jira.

        Args:
          jql_str: The JQL query string.
          page (int): int = 1. Defaults to 1

        Returns:
          A list of issues
        """
        assert page >= 1
        # convert to zero index
        page = page - 1
        max_results: int = kwargs.get("maxResults", 50)
        kwargs["startAt"] = page * max_results
        return super(JiraTask, self).search_issues(jql_str, **kwargs)

    def does_bug_report_exist(self, title) -> Tuple[bool, Optional[Issue]]:
        search = self.search_issues(
            f'Summary ~ "{title}" and Status != {self.final_stage}'
        )
        if search:
            return True, search.pop()
        return False, None

    def create_bug_report(
        self,
        summary: str,
        description: str,
        attachments: Optional[List[Attachment]] = None,
    ) -> Issue:
        """It creates a bug report in Jira.
        If the bug does not exist it creates a new bug report
        otherwise it makes a comment

        Args:
          summary (str): The title of the bug report.
          description (str): The description of the bug.
          attachments: Optional list of Attachment.

        Returns:
          An issue object
        """
        exist, issue = self.does_bug_report_exist(summary)
        if exist:
            self.add_comment(str(issue), description)
        else:
            assert len(summary) > 0
            issue_dict = {
                "project": {"id": self.project_id},
                "summary": summary,
                "description": description,
                "issuetype": {"name": "Bug"},
            }
            issue = self.create_issue(fields=issue_dict)
        if attachments is None:
            attachments = []
        if attachments:
            existing_attachments = {
                existing_atatchment.filename
                for existing_atatchment in issue.get_field("attachment")
            }
            for attachment in attachments:
                if attachment.filename not in existing_attachments:
                    self.add_attachment(
                        issue=issue,
                        attachment=attachment.data,
                        filename=attachment.filename,
                    )
        return issue


def create_connection():
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_TOKEN")
    server = os.environ.get("JIRA_SERVER")
    board_name = os.environ.get("JIRA_BOARD_NAME")
    project_key = os.environ.get("JIRA_PROJECT_KEY")
    # all environment variables must be set
    assert all((email, token, server, board_name, project_key))
    return JiraTask(server, email, token, board_name, project_key)
