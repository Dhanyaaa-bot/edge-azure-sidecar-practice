import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient

# 1. Initialize credentials (uses your active az login automatically)
credential = DefaultAzureCredential()

# 2. Test Key Vault (Hour 2 pattern from Issue #2275)
KV_NAME = os.environ.get("KV_NAME", "kv-dhanya-19068")
vault_url = f"https://{KV_NAME}.vault.azure.net/"
print(f"[1/2] Connecting to Key Vault: {vault_url}...")

secret_client = SecretClient(vault_url=vault_url, credential=credential)
secret = secret_client.get_secret("sidecar-secret")
print(f"✅ Success! Retrieved secret: '{secret.name}' = '{secret.value}'")

# 3. Test Blob Storage (Hour 3 pattern from Issue #2275)
STORAGE_NAME = os.environ.get("STORAGE_NAME", "sadhanya5832")
account_url = f"https://{STORAGE_NAME}.blob.core.windows.net/"
print(f"\n[2/2] Connecting to Blob Storage: {account_url}...")

blob_service = BlobServiceClient(account_url=account_url, credential=credential)
container_client = blob_service.get_container_client("audit-records")

blob_data = b'{"event": "sidecar_audit_ping", "agent": "edge-azure", "status": "active"}'
blob_client = container_client.get_blob_client("test-audit-record.json")
blob_client.upload_blob(blob_data, overwrite=True)

print(f"✅ Success! Uploaded 'test-audit-record.json' to container 'audit-records'.")

# Read it back to verify
downloaded = blob_client.download_blob().readall()
print(f"✅ Verified blob contents: {downloaded.decode('utf-8')}")
