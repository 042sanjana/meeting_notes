from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import sqlite3
import json
import os

from datetime import datetime

from services.speech_to_text import transcribe_audio
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


# ==========================
# Get All Meetings
# ==========================
@router.get("")
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
        DELETE FROM meetings
        WHERE id = ?
        """,
        (meeting_id,)
    )

    conn.commit()

    deleted = cursor.rowcount

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
# Get Tasks
# ==========================
@router.get("/{meeting_id}/tasks")
def get_tasks(
    meeting_id: int
):

    conn = sqlite3.connect(
        "meeting.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT tasks
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

    return json.loads(
        row[0]
    )


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
        """
        ,
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
# Meeting Statistics
# ==========================
@router.get("/stats/overview")
def meeting_stats():

    conn = sqlite3.connect(
        "meeting.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM meetings
        """
    )

    total_meetings = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT tasks
        FROM meetings
        """
    )

    rows = cursor.fetchall()

    total_tasks = 0

    for row in rows:

        try:
            tasks = json.loads(
                row[0]
            )

            total_tasks += len(tasks)

        except:
            pass

    conn.close()

    return {
        "total_meetings": total_meetings,
        "total_tasks": total_tasks
    }


# ==========================
# Reprocess Meeting
# ==========================
@router.post("/{meeting_id}/reprocess")
def reprocess_meeting(
    meeting_id: int
):

    conn = sqlite3.connect(
        "meeting.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT transcript
        FROM meetings
        WHERE id = ?
        """,
        (meeting_id,)
    )

    row = cursor.fetchone()

    if not row:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    transcript = row[0]

    summary = generate_summary(
        transcript
    )

    tasks = extract_tasks(
        transcript
    )

    cursor.execute(
        """
        UPDATE meetings
        SET summary = ?,
            tasks = ?
        WHERE id = ?
        """,
        (
            summary,
            json.dumps(tasks),
            meeting_id
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "meeting_id": meeting_id,
        "summary": summary,
        "tasks": tasks
    }