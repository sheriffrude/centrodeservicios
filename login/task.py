import subprocess
import os
import datetime
from celery import app

@app.task
def backup_databases():
    # Declare variables
    backupDir = "Z:\DireccionTI-Infraestructura\Backups - BD\2024\Abril\bronce"
    dateTime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Create backup for each database
    for dbName in ['DHC', 'intranetcercafe2', 'B_GAF']:
        # Create backup file path
        backupFilePath = os.path.join(backupDir, dbName + "_" + dateTime + ".sql")

        # Run mysqldump command
        subprocess.call(["mysqldump", "--host=192.168.9.200", "--port=3308", "--user=DEV_USER", "--password=DEV-USER12345", dbName, "--result-file=" + backupFilePath])

  
