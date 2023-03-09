Remove-Item -Recurse -Force -Path .venv
python -m venv .venv
.venv/Scripts/Activate.ps1
# pip install pip-tools
pip install -r .\requirements.txt
