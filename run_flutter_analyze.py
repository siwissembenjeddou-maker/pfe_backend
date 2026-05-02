import subprocess
import os

os.chdir(r"c:\autisense\backend\pfe_frontend")
result = subprocess.run(["flutter", "analyze"], capture_output=True, text=True, shell=True)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)
