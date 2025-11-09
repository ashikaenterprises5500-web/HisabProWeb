from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import pandas as pd, io, uuid, xml.etree.ElementTree as ET

app = FastAPI(title="HisabPro Free Web")

DATASETS = {}

@app.get("/")
def home():
    return {"message": "Welcome to HisabPro - Free Online Version!"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
    except Exception:
        return {"error": "Please upload CSV or Excel file only"}

    records = []
    for _, r in df.iterrows():
        records.append({
            "invoice": str(r.get("Invoice", "")),
            "date": str(r.get("Date", "")),
            "vendor": str(r.get("Vendor", "")),
            "amount": float(r.get("Amount", 0)),
            "gst": float(r.get("GST", 0)),
            "tds": float(r.get("TDS", 0)),
            "type": str(r.get("Type", "Sale"))
        })
    dataset_id = str(uuid.uuid4())
    DATASETS[dataset_id] = records
    return {"dataset_id": dataset_id, "rows": len(records)}

@app.get("/api/export/{dataset_id}")
def export_xml(dataset_id: str):
    data = DATASETS.get(dataset_id)
    if not data:
        return JSONResponse({"error": "Dataset not found"}, status_code=404)
    root = ET.Element("ENVELOPE")
    for e in data:
        v = ET.SubElement(root, "VOUCHER")
        ET.SubElement(v, "DATE").text = e["date"]
        ET.SubElement(v, "NARRATION").text = f"{e['type']} {e['invoice']}"
        ET.SubElement(v, "AMOUNT").text = str(e["amount"])
    xml = ET.tostring(root, encoding="unicode")
    return {"tally_xml": xml}
