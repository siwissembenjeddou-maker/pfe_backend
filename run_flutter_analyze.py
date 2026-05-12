import subprocess
import os

# Run from this script to avoid PowerShell command parsing issues.
os.chdir(r"c:\autisense\backend\pfe_frontend")

result = subprocess.run(
    ["flutter", "analyze"],
    capture_output=True,
    text=True,
    shell=False,
)

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)

