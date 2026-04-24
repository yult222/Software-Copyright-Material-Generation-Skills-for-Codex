"""Tiny demo application for SoftCopy repository scanning."""


USERS = {"demo": "reader"}


def login(username: str, password: str) -> bool:
    return USERS.get(username) == password


def create_document(title: str, body: str) -> dict[str, str]:
    return {"title": title.strip(), "body": body.strip(), "status": "draft"}


def publish_document(document: dict[str, str]) -> dict[str, str]:
    published = dict(document)
    published["status"] = "published"
    return published


def list_reports() -> list[str]:
    return ["draft-count", "published-count", "user-activity"]


if __name__ == "__main__":
    print(create_document("Demo", "SoftCopy workflow"))
