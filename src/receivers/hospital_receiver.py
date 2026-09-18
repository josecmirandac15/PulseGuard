from fastapi import FastAPI, Request
from datetime import datetime

app = FastAPI(title="Hospital Receiver")

print("\n" + "="*60)
print("🏥 HOSPITAL RECEIVER - Running on port 8001")
print("="*60 + "\n")


@app.post("/webhook/hospital")
async def receive_notification(request: Request):
    payload = await request.json()

    print("\n" + "-"*60)
    print("📨 NOTIFICATION RECEIVED - HOSPITAL ADMISSIONS DEPT")
    print("-"*60)
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Admission ID: {payload.get('admission_id')}")
    print(f"   Patient ID: {payload.get('patient_id')}")
    print(f"   Policy Number: {payload.get('policy_number')}")
    print(f"   Hospital Code: {payload.get('hospital_code')}")
    print(f"   Reason: {payload.get('admission_reason')}")

    if "alert" in payload:
        alert = payload["alert"]
        print(f"\n   ALERT LEVEL: {alert.get('level', 'N/A').upper()}")
        print(f"   Message: {alert.get('message')}")
        if alert.get("recommendations"):
            print("   Recommendations:")
            for rec in alert["recommendations"]:
                print(f"     - {rec}")

    print("-"*60)
    print("✅ Notification processed by Hospital Admissions")
    print("-"*60 + "\n")

    return {"status": "received", "receiver": "hospital"}


@app.get("/health")
async def health():
    return {"status": "healthy", "receiver": "hospital"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
