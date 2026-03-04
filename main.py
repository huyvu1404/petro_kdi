from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.responses import FileResponse
import os
import uuid
import json

from src.petro import process_zip_excel
from src.kdi import generate_kdi_report
from src.utils import cleanup
app = FastAPI()


# ===================== API =====================
@app.post("/petro/filter-columns")
async def filter_columns(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    columns: str = Form(...),
):
    print(f"Received file: {file.filename}, columns: {columns}")

    work_dir = f"tmp/{uuid.uuid4()}"
    os.makedirs(work_dir, exist_ok=True)

    if not file.filename.endswith(".zip"):
        cleanup(work_dir)
        raise HTTPException(status_code=400, detail="File phải là .zip")

    try:
        # ---------- Parse columns (CSV hoặc JSON array) ----------
        try:
            parsed = json.loads(columns)
            if isinstance(parsed, list):
                selected_columns = [str(c).strip() for c in parsed]
            else:
                raise ValueError
        except Exception:
            selected_columns = [c.strip() for c in columns.split(",") if c.strip()]

        if not selected_columns:
            raise HTTPException(
                status_code=400,
                detail="Danh sách cột không hợp lệ"
            )

        # ---------- Save zip ----------
        input_zip = os.path.join(work_dir, file.filename)
        with open(input_zip, "wb") as f:
            f.write(await file.read())

        # ---------- Process ----------
        result_zip = process_zip_excel(
            zip_path=input_zip,
            work_dir=work_dir,
            selected_columns=selected_columns,
        )

        # ---------- Cleanup after response ----------
        background_tasks.add_task(cleanup, work_dir)

        return FileResponse(
            result_zip,
            media_type="application/zip",
            filename="result.zip",
            background=background_tasks,
        )

    except HTTPException:
        cleanup(work_dir)
        raise

    except Exception as e:
        cleanup(work_dir)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/kdi/generate-report")
async def generate_report(
    background_tasks: BackgroundTasks,
    report_type: str = Form(...),
    file: UploadFile = File(...),
    last_week_file: UploadFile | None = File(None)
):
    print("Received:", report_type)
    print("receive", file.filename)
    if report_type not in {"daily", "weekly"}:
        raise HTTPException(400, "report_type must be daily or weekly")

    if not file.filename.endswith(".zip"):
        raise HTTPException(400, "file must be a .zip")

    if last_week_file and not last_week_file.filename.endswith(".zip"):
        raise HTTPException(400, "last_week_file must be a .zip")

    work_dir = f"tmp/{uuid.uuid4()}"
    os.makedirs(work_dir, exist_ok=True)

    try:
        current_zip = os.path.join(work_dir, "current.zip")
        with open(current_zip, "wb") as f:
            f.write(await file.read())

        last_week_zip = None
        if last_week_file:
            last_week_zip = os.path.join(work_dir, "last_week.zip")
            with open(last_week_zip, "wb") as f:
                f.write(await last_week_file.read())

        zip_output_path, _ = generate_kdi_report(
            zip_path=current_zip,
            work_dir=work_dir,
            report_type=report_type,
            last_week_zip=last_week_zip
        )

    except Exception as e:
        cleanup(work_dir)
        raise HTTPException(400, str(e))

    background_tasks.add_task(cleanup, work_dir)

    return FileResponse(
        zip_output_path,
        media_type="application/zip",
        filename="report.zip"
    )
