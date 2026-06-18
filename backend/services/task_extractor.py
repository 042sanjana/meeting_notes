import re
import dateparser


def extract_tasks(transcript):

    tasks = []

    patterns = [

        # John, complete task by Thursday.
        r"(\w+),\s*(.*?)\s+by\s+(.*?)[.]",

        # John will complete task by Thursday.
        r"(\w+)\s+will\s+(.*?)\s+by\s+(.*?)[.]",

        # John should complete task by Thursday.
        r"(\w+)\s+should\s+(.*?)\s+by\s+(.*?)[.]"
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            transcript,
            re.IGNORECASE
        )

        for person, task, deadline in matches:

            parsed_date = dateparser.parse(
                deadline,
                settings={
                    "PREFER_DATES_FROM": "future"
                }
            )

            deadline_date = None

            if parsed_date:
                deadline_date = parsed_date.strftime(
                    "%Y-%m-%d"
                )

            tasks.append({
                "owner": person.strip(),
                "task": task.strip(),
                "deadline_text": deadline.strip(),
                "deadline_date": deadline_date
            })

    return tasks