import asyncio
import json
from datetime import datetime
from pathlib import Path

TESTS_FILE = Path("tests.json")
RESULTS_FILE = Path("results.json")
_results_lock = asyncio.Lock()


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


async def save_test_result(
    user_id: int,
    full_name: str,
    username: str | None,
    test_id: str,
    test_title: str,
    score: int,
    total_questions: int,
) -> dict:
  async with _results_lock:
    results = []
    if RESULTS_FILE.exists():
      content = RESULTS_FILE.read_text(encoding="utf-8").strip()
      if content:
        results = json.loads(content)

    # Takroriy natija yozmaslik uchun shu yerning o'zida (lock ichida) tekshiramiz
    for item in results:
      if item.get("user_id") == user_id and item.get("test_id") == test_id:
        return item

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

    # Avval vaqtinchalik faylga yozib, keyin almashtirish (atomic replace)
    temp_file = RESULTS_FILE.with_suffix(".tmp")
    temp_file.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temp_file.replace(RESULTS_FILE)
    return entry


def get_user_test_result(user_id: int, test_id: str) -> dict | None:
  """Agar foydalanuvchi ushbu testni avval ishlagan bo'lsa, natija yozuvini qaytaradi."""
  results = load_results()
  for entry in results:
    if entry.get("user_id") == user_id and entry.get("test_id") == test_id:
      return entry
  return None
