from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import File
from fastapi import HTTPException

import shutil
import sqlite3
import json
import os

from datetime import datetime

from services.text_to_speech import (
    transcribe_audio
)

from services.summarizer import (
    generate_summary
)

from services.task_extractor import (
    extract_tasks
)

router = APIRouter(
    prefix="/meetings",
    tags=["Meetings"]
)

os.makedirs(
    "uploads",
    exist_ok=True
)


@router.post("/upload")
async def upload_meeting(
    file: UploadFile = File(...)
):
    try:

        file_path = os.path.join(
            "uploads",
            file.filename
        )

        with open(
            file_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        # Whisper
        transcript = transcribe_audio(
            file_path
        )

        # BART
        summary = generate_summary(
            transcript
        )

        # Regex
        tasks = extract_tasks(
            transcript
        )

        conn = sqlite3.connect(
            "meeting.db"
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO meetings(
                file_name,
                transcript,
                summary,
                tasks,
                created_at
            )
            VALUES(?,?,?,?,?)
            """,
            (
                file.filename,
                transcript,
                summary,
                json.dumps(tasks),
                str(datetime.now())
            )
        )

        meeting_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return {
            "success": True,
            "meeting_id": meeting_id,
            "file_name": file.filename,
            "transcript": transcript,
            "summary": summary,
            "tasks": tasks
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/")
def get_all_meetings():

    conn = sqlite3.connect(
        "meeting.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
        id,
        file_name,
        summary,
        created_at
        FROM meetings
        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()

    conn.close()

    meetings = []

    for row in rows:

        meetings.append(
            {
                "id": row[0],
                "file_name": row[1],
                "summary": row[2],
                "created_at": row[3]
            }
        )

    return meetings


@router.get("/{meeting_id}")
def get_meeting(
    meeting_id: int
):

    conn = sqlite3.connect(
        "meeting.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM meetings
        WHERE id = ?
        """,
        (meeting_id,)
    )

    row = cursor.fetchone()

    conn.close()

    if not row:

        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    return {
        "id": row[0],
        "file_name": row[1],
        "transcript": row[2],
        "summary": row[3],
        "tasks": json.loads(row[4]),
        "created_at": row[5]
    }


@router.delete("/{meeting_id}")
def delete_meeting(
    meeting_id: int
):

    conn = sqlite3.connect(
        "meeting.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM meetings
        WHERE id = ?
        """,
        (meeting_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Meeting deleted successfully"
    }