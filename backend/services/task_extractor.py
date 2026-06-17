import re

TASK_KEYWORDS = [
    "complete",
    "finish",
    "prepare",
    "submit",
    "review",
    "test",
    "develop",
    "create"
]

def extract_tasks(
        transcript
):

    tasks = []

    sentences = re.split(
        r'[.\n]',
        transcript
    )

    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue

        for keyword in TASK_KEYWORDS:

            if keyword in sentence.lower():

                deadline = None

                deadline_match = re.search(
                    r'by\s+([A-Za-z]+)',
                    sentence,
                    re.IGNORECASE
                )

                if deadline_match:

                    deadline = deadline_match.group(1)

                tasks.append(
                    {
                        "task": sentence,
                        "deadline": deadline
                    }
                )

                break

    return tasks

