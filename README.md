poetry env use 3.12
source $(poetry env info --path)/bin/activate
poetry shell
fastapi dev focus_track_api/app.py