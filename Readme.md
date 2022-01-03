python3 -m venv venv
source venv/bin/activate

pip install fastapi
pip install uvicorn
pip install tortoise-orm
pip install fastapi-mail
pip install python-dotenv
pip install pyjwt
pip install python-multipart
python3 -m pip install --upgrade Pillow
pip install aiofiles

uvicorn main:app --reload

pip freeze > requirements.txt