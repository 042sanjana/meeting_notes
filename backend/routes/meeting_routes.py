from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import sqlite3
import json
import os

from datetime import datetime

from services.text_to_speech import transcribe_audio
from services.summarizer import generate_summary
from services.task_extractor import extract_tasks

router = APIRouter(
    prefix="/meetings",
    tags=["Meetings"]
)

os.makedirs(
    "uploads",
    exist_ok=True
)


# ==========================
# Upload Meeting
# ==========================
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

        transcript = transcribe_audio(
            file_path
        )

        summary = generate_summary(
            transcript
        )

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

        for task in tasks:

            cursor.execute(
                """
                INSERT INTO tasks(
                    meeting_id,
                    owner,
                    task,
                    deadline_text,
                    deadline_date,
                    priority,
                    status,
                    created_at
                )
                VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    meeting_id,
                    task["owner"],
                    task["task"],
                    task["deadline_text"],
                    task["deadline_date"],
                    task["priority"],
                    task["status"],
                    str(datetime.now())
                )
            )

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

@router.get("/{meeting_id}/tasks")
def get_meeting_tasks(meeting_id: int):

    conn = sqlite3.connect("meeting.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            owner,
            task,
            deadline_date,
            priority,
            status
        FROM tasks
        WHERE meeting_id = ?
        ORDER BY deadline_date
    """, (meeting_id,))

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "owner": row[0],
            "task": row[1],
            "deadline_date": row[2],
            "priority": row[3],
            "status": row[4]
        }
        for row in rows
    ]
@router.get("/latest/tasks")
def latest_tasks():

    conn = sqlite3.connect("meeting.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT MAX(id)
        FROM meetings
    """)

    latest_id = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            owner,
            task,
            deadline_date,
            priority,
            status
        FROM tasks
        WHERE meeting_id = ?
    """, (latest_id,))

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "owner": row[0],
            "task": row[1],
            "deadline_date": row[2],
            "priority": row[3],
            "status": row[4]
        }
        for row in rows
    ]
# ==========================
# Search Meetings
# ==========================
@router.get("/search/{keyword}")
def search_meetings(
    keyword: str
):

    conn = sqlite3.connect(
        "meeting.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            file_name,
            summary
        FROM meetings
        WHERE transcript LIKE ?
        OR summary LIKE ?
        """,
        (
            f"%{keyword}%",
            f"%{keyword}%"
        )
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "file_name": row[1],
            "summary": row[2]
        }
        for row in rows
    ]


# ==========================
# Get All Meetings
# ==========================
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

    return [
        {
            "id": row[0],
            "file_name": row[1],
            "summary": row[2],
            "created_at": row[3]
        }
        for row in rows
    ]


# ==========================
# Get Meeting By ID
# ==========================
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


# ==========================
# Update Summary
# ==========================
@router.put("/{meeting_id}/summary")
def update_summary(
    meeting_id: int,
    summary: str
):

    conn = sqlite3.connect(
        "meeting.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE meetings
        SET summary = ?
        WHERE id = ?
        """,
        (
            summary,
            meeting_id
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Summary updated successfully"
    }


# ==========================
# Delete Meeting
# ==========================
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
        DELETE FROM tasks
        WHERE meeting_id = ?
        """,
        (meeting_id,)
    )

    cursor.execute(
        """
        DELETE FROM meetings
        WHERE id = ?
        """,
        (meeting_id,)
    )

    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    if deleted == 0:

        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    return {
        "success": True,
        "message": "Meeting deleted successfully"
    }