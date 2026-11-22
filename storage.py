from datetime import datetime
import json
from pathlib import Path

TESTS_FILE = Path("tests.json")
RESULTS_FILE = Path("results.json")


def load_tests() -> dict:
  if not TESTS_FILE.exists():
    return {}
  with TESTS_FILE.open("r", encoding="utf-8") as f:
    content = f.read().strip()
    return json.loads(content) if content else {}


def get_test_by_id(test_id: str) -> dict | None:
  tests = load_tests()
  return tests.get(test_id)


def save_test(title: str, questions: list[dict]) -> str:
  tests = load_tests()
  # Takrorlanmas test_id hosil qilish
  num = len(tests) + 1
  test_id = f"test_{num}"
  while test_id in tests:
    num += 1
    test_id = f"test_{num}"

  tests[test_id] = {
      "title": title,
      "questions": questions,
  }
  with TESTS_FILE.open("w", encoding="utf-8") as f:
    json.dump(tests, f, ensure_ascii=False, indent=2)
  return test_id


def load_results() -> list[dict]:
  if not RESULTS_FILE.exists():
    return []
  with RESULTS_FILE.open("r", encoding="utf-8") as f:
    content = f.read().strip()
    return json.loads(content) if content else []


def save_test_result(
    user_id: int,
    full_name: str,
    username: str | None,
    test_id: str,
    test_title: str,
    score: int,
    total_questions: int,
) -> dict:
  results = load_results()
  entry = {
      "user_id": user_id,
      "full_name": full_name,
      "username": username,
      "test_id": test_id,
      "test_title": test_title,
      "score": score,
      "total_questions": total_questions,
      "finished_at": datetime.now().isoformat(timespec="seconds"),
  }
  results.append(entry)

  with RESULTS_FILE.open("w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

  return entry