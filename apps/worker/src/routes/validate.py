import json

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from src.core.validation import validate_epub
from src.storage.jobs import JobStore

router = APIRouter(prefix="/v1", tags=["validation"])
job_store = JobStore()


@router.post("/validate")
async def validate_file(request: Request, file: UploadFile = File(...)) -> dict:
    filename = file.filename or "upload.epub"
    if not filename.lower().endswith(".epub"):
        raise HTTPException(status_code=415, detail="Only EPUB uploads are supported in the current validation slice.")

    payload = await file.read()
    job_id, epub_path = job_store.create_job(filename, payload)
    artifacts_base_url = str(request.base_url).rstrip("/") + "/v1/artifacts"
    result = validate_epub(str(epub_path), job_id, artifacts_base_url)

    job_store.write_json_artifact(job_id, "report.json", result.model_dump(by_alias=True))
    job_store.write_text_artifact(job_id, "report.html", _render_html_report(result.model_dump(by_alias=True)))
    return result.model_dump(by_alias=True)


def _render_html_report(result: dict) -> str:
    rows = "\n".join(
        (
            "<tr>"
            f"<td>{message['severity']}</td>"
            f"<td>{message['id']}</td>"
            f"<td>{message['file']}</td>"
            f"<td>{message['message']}</td>"
            f"<td>{message.get('suggestion') or ''}</td>"
            "</tr>"
        )
        for message in result["messages"]
    )
    pretty_counts = json.dumps(result["counts"], indent=2)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>EpubDoctor Validation Report</title>
    <style>
      body {{ font-family: sans-serif; margin: 2rem; background: #0f1720; color: #f8fafc; }}
      table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
      th, td {{ border: 1px solid #334155; padding: 0.6rem; text-align: left; vertical-align: top; }}
      code {{ background: #1e293b; padding: 0.2rem 0.4rem; border-radius: 0.3rem; }}
    </style>
  </head>
  <body>
    <h1>EpubDoctor Validation Report</h1>
    <p><strong>Job:</strong> <code>{result['jobId']}</code></p>
    <p><strong>EPUB version:</strong> {result['epubVersion']}</p>
    <pre>{pretty_counts}</pre>
    <table>
      <thead>
        <tr>
          <th>Severity</th>
          <th>ID</th>
          <th>File</th>
          <th>Message</th>
          <th>Suggestion</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  </body>
</html>"""
