import os
from pytfe import TFEClient


def main():
    token = os.getenv("TFE_TOKEN")
    task_result_id = os.getenv("TFE_TASK_RESULT_ID")

    if not token:
        print("Set TFE_TOKEN")
        return

    if not task_result_id:
        print("Set TFE_TASK_RESULT_ID")
        return

    client = TFEClient()

    try:
        result = client.task_results.read(task_result_id)

        print("=== Task Result ===")
        print(f"ID: {result.id}")
        print(f"Status: {result.status}")
        print(f"Message: {result.message}")
        print(f"Task Name: {result.task_name}")
        print(f"URL: {result.url}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()