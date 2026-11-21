import json
import uuid
import datetime
import logging
import threading
import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient
from opencensus.ext.azure.log_exporter import AzureLogHandler

# --- CONFIGURATION (Zero hardcoded secrets!) ---
VAULT_URL = "https://kv-dhanya-19068.vault.azure.net/"
STORAGE_URL = "https://sadhanya5832.blob.core.windows.net/"
CONTAINER_NAME = "audit-records"
APP_INSIGHTS_CONN = "InstrumentationKey=a17dfd23-4e73-4c08-9c38-fee8f985f5b9;IngestionEndpoint=https://centralindia-0.in.applicationinsights.azure.com/;LiveEndpoint=https://centralindia.livediagnostics.monitor.azure.com/;ApplicationId=72f17a04-fc3a-4fb7-b725-270cd1f829ae"

# --- APPLICATION INSIGHTS LOGGER SETUP ---
logger = logging.getLogger("EdgeAzureSidecar")
logger.setLevel(logging.INFO)
try:
    azure_handler = AzureLogHandler(connection_string=APP_INSIGHTS_CONN)
    azure_handler.lock = threading.RLock()
    logger.addHandler(azure_handler)
except Exception as e:
    logging.warning(f"Failed to attach AzureLogHandler: {e}")

# --- INITIALIZE AZURE FUNCTION APP ---
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="sidecar_audit", methods=["POST", "GET"])
def sidecar_audit(req: func.HttpRequest) -> func.HttpResponse:
    logger.info("⚡ [Sidecar] Received incoming audit trigger request.")
    
    # 1. Parse request body
    try:
        req_body = req.get_json() if req.get_body() else {}
    except ValueError:
        req_body = {}
    
    event_name = req_body.get("event", "codeslice_sidecar_ping")
    agent_id = req_body.get("agent", "edge-azure-agent")
    
    try:
        # 2. Keyless Authentication via DefaultAzureCredential
        credential = DefaultAzureCredential()
        
        # 3. Retrieve secret from Key Vault
        secret_client = SecretClient(vault_url=VAULT_URL, credential=credential)
        secret = secret_client.get_secret("sidecar-secret")
        logger.info(f"🔑 [Sidecar] Successfully verified secret '{secret.name}' from Key Vault.")
        
        # 4. Prepare Audit Record Payload
        record_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        audit_payload = {
            "record_id": record_id,
            "timestamp": timestamp,
            "event": event_name,
            "agent": agent_id,
            "keyvault_verified": True,
            "secret_version": secret.properties.version,
            "status": "COMPLIANCE_COMMITTED"
        }
        
        # 5. Upload to Blob Storage
        blob_service = BlobServiceClient(account_url=STORAGE_URL, credential=credential)
        container_client = blob_service.get_container_client(CONTAINER_NAME)
        blob_name = f"audit-{record_id[:8]}.json"
        blob_client = container_client.get_blob_client(blob_name)
        
        blob_data = json.dumps(audit_payload, indent=2).encode('utf-8')
        blob_client.upload_blob(blob_data, overwrite=True)
        logger.info(f"💾 [Sidecar] Persisted audit record '{blob_name}' to container '{CONTAINER_NAME}'.")
        
        # 6. Return Structured JSON Receipt
        response_data = {
            "status": "SUCCESS",
            "message": "Sidecar audit record verified and committed to Azure.",
            "record_id": record_id,
            "blob_name": blob_name,
            "blob_url": f"{STORAGE_URL}{CONTAINER_NAME}/{blob_name}",
            "vault": "kv-dhanya-19068"
        }
        return func.HttpResponse(
            body=json.dumps(response_data, indent=2),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        error_msg = f"❌ [Sidecar Error] Execution failed: {str(e)}"
        logger.error(error_msg)
        return func.HttpResponse(
            body=json.dumps({"status": "ERROR", "error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
