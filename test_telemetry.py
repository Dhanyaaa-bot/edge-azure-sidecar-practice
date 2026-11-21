import os
import time
import logging
import threading
from opencensus.ext.azure.log_exporter import AzureLogHandler

# Connection string for func-sidecar-dhanya-1890
CONN_STR = "InstrumentationKey=a17dfd23-4e73-4c08-9c38-fee8f985f5b9;IngestionEndpoint=https://centralindia-0.in.applicationinsights.azure.com/;LiveEndpoint=https://centralindia.livediagnostics.monitor.azure.com/;ApplicationId=72f17a04-fc3a-4fb7-b725-270cd1f829ae"

logger = logging.getLogger("CodeSliceSidecar")
logger.setLevel(logging.INFO)

# 1. Initialize handler
azure_handler = AzureLogHandler(connection_string=CONN_STR)

# 2. Fix for Python 3.14 lock compatibility
azure_handler.lock = threading.RLock()

logger.addHandler(azure_handler)

print("📡 Connecting to Azure Application Insights...")
logger.info("🚀 [Sidecar Telemetry] CodeSlice Edge-Azure Sidecar initialized.")
logger.warning("⚠️ [Sidecar Telemetry] High load warning test on container 'audit-records'.")
logger.info("✅ [Sidecar Telemetry] Processed audit record for Dhanya.")

print("Flushing logs to Azure (waiting 10s)...")
time.sleep(10)
print("🎯 Done! Telemetry logs successfully sent.")
