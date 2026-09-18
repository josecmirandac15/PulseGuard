from fastapi import FastAPI, Request
from datetime import datetime

app = FastAPI(title="Insurer Receiver")

print("\n" + "="*60)
print("🏢 INSURER RECEIVER - Running on port 8002")
print("="*60 + "\n")


@app.post("/webhook/insurer")
async def receive_notification(request: Request):
    payload = await request.json()

    print("\n" + "-"*60)
    print("📨 NOTIFICATION RECEIVED - INSURER CASE MANAGER")
    print("-"*60)
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Admission ID: {payload.get('admission_id')}")
    print(f"   Patient ID: {payload.get('patient_id')}")
    print(f"   Policy Number: {payload.get('policy_number')}")
    print(f"   Reason: {payload.get('admission_reason')}")

    requires_review = payload.get("requires_case_manager_review", False)
    if requires_review:
        print(f"\n   ⚠️  CASE MANAGER REVIEW REQUIRED")
    else:
        print(f"\n   ℹ️  No case manager review needed")

    if "alert" in payload:
        alert = payload["alert"]
        print(f"\n   ALERT LEVEL: {alert.get('level', 'N/A').upper()}")
        print(f"   Message: {alert.get('message')}")
        if alert.get("agent_analysis"):
            print(f"   Analysis: {alert.get('agent_analysis')}")
        if alert.get("recommendations"):
            print("   Recommendations:")
            for rec in alert["recommendations"]:
                print(f"     - {rec}")

    print("-"*60)
    print("✅ Notification processed by Insurance Case Manager")
    print("-"*60 + "\n")

    return {"status": "received", "receiver": "insurer"}


@app.get("/health")
async def health():
    return {"status": "healthy", "receiver": "insurer"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
