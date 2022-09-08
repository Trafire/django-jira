import io
import os

from django_jira.tasks.tasks import Attachment, JiraTask  # type: ignore


def test_authentication():
    get_boards()


def get_boards():
    email = os.environ.get("jira_email")
    token = os.environ.get("jira_token")
    server = os.environ.get("jira_server")
    board_name = os.environ.get("jira_board_name")
    project_key = os.environ.get("jira_project_key")
    return JiraTask(server, email, token, board_name, project_key)


def test_attachment_in_memory():
    a = Attachment(filename="hello.txt", data=io.BytesIO(b""))
    assert a.filepath is None
    assert a.filename == "hello.txt"


def test_atatchment_filetmp_path(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text("CONTENT")
    a = Attachment(filepath=str(p))
    assert a.filepath.endswith("hello.txt")
