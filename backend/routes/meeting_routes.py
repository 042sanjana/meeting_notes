
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Depends
)
import shutil
import sqlite3
import json
import os
import dateparser
from fastapi.responses import FileResponse
import tempfile
from datetime import datetime, timedelta
from security import get_current_user
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
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):

    try:

        user_id = current_user["id"]

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
                user_id,
                file_name,
                transcript,
                summary,
                tasks,
                created_at
            )
            VALUES(?,?,?,?,?,?)
            """,
            (
                user_id,
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
@router.get("/tasks/export/{user_id}")
def export_user_tasks(user_id: int):

    conn = sqlite3.connect("meeting.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            t.task,
            t.owner,
            t.deadline_date,
            t.priority
        FROM tasks t
        INNER JOIN meetings m
            ON t.meeting_id = m.id
        WHERE m.user_id = ?
        """,
        (user_id,)
    )

    tasks = cursor.fetchall()
    conn.close()

    if not tasks:
        raise HTTPException(
            status_code=404,
            detail="No tasks found"
        )

    ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//AI Meeting Notes//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
"""

    for task in tasks:

        task_name = task[0]
        owner = task[1]
        deadline = task[2]
        priority = task[3]

        try:

            if not deadline:
                continue

            if "-" in deadline:

                parts = deadline.split("-")

                # Format: YYYY-MM-DD
                if len(parts[0]) == 4:

                    dt = datetime.strptime(
                        deadline[:10],
                        "%Y-%m-%d"
                    )

                # Format: DD-MM-YYYY
                else:

                    dt = datetime.strptime(
                        deadline[:10],
                        "%d-%m-%Y"
                    )

            else:
                continue

        except Exception:
            continue

        # Create all-day calendar event
        start_date = dt.strftime("%Y%m%d")

        end_date = (
            dt + timedelta(days=1)
        ).strftime("%Y%m%d")

        ics_content += f"""
BEGIN:VEVENT
SUMMARY:{task_name}
DESCRIPTION:Owner: {owner} | Priority: {priority}
DTSTART;VALUE=DATE:{start_date}
DTEND;VALUE=DATE:{end_date}

BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:Reminder - {task_name}
TRIGGER:-P1D
END:VALARM

END:VEVENT
"""

    ics_content += """
END:VCALENDAR
"""

    file_path = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".ics"
    ).name

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(ics_content)

    return FileResponse(
        path=file_path,
        media_type="text/calendar",
        filename=f"user_{user_id}_tasks.ics"
    )


@router.put("/tasks/{task_id}/status")
def update_task_status(
    task_id: int,
    status: str
):

    conn = sqlite3.connect("meeting.db")

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET status = ?
        WHERE id = ?
        """,
        (
            status,
            task_id
        )
    )

    conn.commit()

    updated_rows = cursor.rowcount

    conn.close()

    if updated_rows == 0:

        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return {
        "success": True,
        "task_id": task_id,
        "status": status
    }

    
@router.put("/tasks/{task_id}/deadline")
def update_task_deadline(
    task_id: int,
    deadline_date: str
):

    conn = sqlite3.connect("meeting.db")

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET deadline_date = ?
        WHERE id = ?
        """,
        (
            deadline_date,
            task_id
        )
    )

    conn.commit()

    updated_rows = cursor.rowcount

    conn.close()

    if updated_rows == 0:

        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return {
        "success": True,
        "task_id": task_id,
        "deadline_date": deadline_date
    }
    
@router.get("/{meeting_id}/tasks")
def get_meeting_tasks(meeting_id: int):

    conn = sqlite3.connect("meeting.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM tasks
        WHERE meeting_id = ?
        ORDER BY deadline_date
    """, (meeting_id,))

    rows = cursor.fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]
    
    
@router.get("/user/{user_id}/tasks")
def get_user_tasks(user_id: int):

    conn = sqlite3.connect("meeting.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT t.*
        FROM tasks t
        INNER JOIN meetings m
        ON t.meeting_id = m.id
        WHERE m.user_id = ?
        ORDER BY t.deadline_date
    """, (user_id,))

    rows = cursor.fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]
    
    

    
    
@router.get("/tasks")
def get_all_tasks():

    conn = sqlite3.connect("meeting.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM tasks
        ORDER BY deadline_date
    """)

    rows = cursor.fetchall()

    conn.close()

    return [
        dict(row)
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
@router.get("/user/{user_id}")
def get_user_meetings(user_id: int):

    conn = sqlite3.connect("meeting.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            file_name,
            summary,
            created_at
        FROM meetings
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
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
    
    
    
   