"""Tiny demo application for SoftCopy repository scanning."""

USERS = {"demo": "reader", "author": "writer"}
DOCUMENTS: list[dict[str, str]] = []


def login(username: str, password: str) -> bool:
    return USERS.get(username) == password


def create_document(title: str, body: str) -> dict[str, str]:
    document = {"title": title.strip(), "body": body.strip(), "status": "draft"}
    DOCUMENTS.append(document)
    return document


def update_document(document: dict[str, str], title: str, body: str) -> dict[str, str]:
    document["title"] = title.strip()
    document["body"] = body.strip()
    return document


def validate_document(document: dict[str, str]) -> list[str]:
    errors: list[str] = []
    if not document.get("title"):
        errors.append("title is required")
    if not document.get("body"):
        errors.append("body is required")
    return errors


def publish_document(document: dict[str, str]) -> dict[str, str]:
    if validate_document(document):
        document["status"] = "blocked"
        return document
    document["status"] = "published"
    return document


def archive_document(document: dict[str, str]) -> dict[str, str]:
    document["status"] = "archived"
    return document


def list_documents(status: str | None = None) -> list[dict[str, str]]:
    if status is None:
        return list(DOCUMENTS)
    return [item for item in DOCUMENTS if item.get("status") == status]


def search_documents(keyword: str) -> list[dict[str, str]]:
    normalized = keyword.lower()
    return [item for item in DOCUMENTS if normalized in item.get("title", "").lower()]


def summarize_document(document: dict[str, str]) -> str:
    return f"{document.get('title', '')}: {document.get('status', '')}"


def count_by_status() -> dict[str, int]:
    summary: dict[str, int] = {}
    for document in DOCUMENTS:
        status = document.get("status", "unknown")
        summary[status] = summary.get(status, 0) + 1
    return summary


def list_reports() -> list[str]:
    return ["draft-count", "published-count", "user-activity"]


def generate_report(name: str) -> dict[str, object]:
    if name == "draft-count":
        return {"name": name, "value": count_by_status().get("draft", 0)}
    if name == "published-count":
        return {"name": name, "value": count_by_status().get("published", 0)}
    return {"name": name, "value": len(DOCUMENTS)}


def export_document(document: dict[str, str]) -> str:
    return f"# {document.get('title', '')}\n\n{document.get('body', '')}"


def import_document(payload: str) -> dict[str, str]:
    title, _, body = payload.partition("\n")
    return create_document(title.strip("# "), body.strip())


def reset_demo_state() -> None:
    DOCUMENTS.clear()


DEMO_EVENTS = [
    "open-project",
    "seed-state",
    "create-guide",
    "create-notes",
    "validate-guide",
    "validate-notes",
    "publish-guide",
    "archive-draft",
    "list-all",
    "list-published",
    "search-guide",
    "search-release",
    "summarize-guide",
    "summarize-notes",
    "count-draft",
    "count-published",
    "count-archived",
    "report-draft",
    "report-published",
    "report-activity",
    "export-guide",
    "export-notes",
    "import-guide",
    "import-notes",
    "reset-state",
    "run-main",
    "print-report",
    "finish-demo",
    "ready-eval",
]


def seed_demo_state() -> None:
    reset_demo_state()
    create_document("Demo Guide", "SoftCopy workflow introduction")
    create_document("Release Notes", "Generated materials are reviewable")


def main() -> None:
    seed_demo_state()
    publish_document(DOCUMENTS[0])
    print(generate_report("published-count"))


if __name__ == "__main__":
    main()
