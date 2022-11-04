import io
import os

from django_jira.tasks.tasks import Attachment, JiraTask  # type: ignore


def test_authentication():
    get_boards()


def get_boards():
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_TOKEN")
    server = os.environ.get("JIRA_SERVER")
    board_name = os.environ.get("JIRA_BOARD_NAME")
    project_key = os.environ.get("JIRA_PROJECT_KEY")
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
