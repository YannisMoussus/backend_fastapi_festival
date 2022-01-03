from fastapi import FastAPI, BackgroundTasks, Form, Depends, Request, HTTPException, status
from fastapi import responses
from starlette.requests import Request
from starlette.responses import HTMLResponse
from tortoise.contrib.fastapi import register_tortoise


#self packages
from models import *
from emails import *


#Authentication
from authentication import *
from fastapi.security import(OAuth2PasswordBearer, OAuth2PasswordRequestForm, oauth2)


#signals
from tortoise.signals import post_save
from typing import List, Optional, Type
from tortoise import BaseDBAsyncClient


#response classes
from fastapi.responses import HTMLResponse


#templates
from fastapi.templating import Jinja2Templates


#image upload
from fastapi import File, UploadFile
import secrets
from fastapi.staticfiles import StaticFiles
from PIL import Image


#datetime
from datetime import datetime


app = FastAPI()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl= 'token')



#static file setup config
app.mount("/static", StaticFiles(directory="static"), name="static")



@app.post('/token')
async def generate_token(request_form: OAuth2PasswordRequestForm = Depends()):
    token = await token_generator(request_form.username, request_form.password)
    return {"access_token" : token, "token_type" : "bearer"}


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, config_credential["SECRET"], algorithms=['HS256'])
        user = await User.get(id = payload.get("id"))
    except:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid username or password",
            headers= {"WWW-Authenticate" : "Bearer"}
        )
    return await user


@app.post("/user/me")
async def user_login(user: user_pydanticIn = Depends(get_current_user)):
    festival = await Festival.get(owner = user)
    logo = festival.logo #4567Fgfrt.png
    logo_path = "localhost:8000/static/images/"+logo

    return {
        "status" : "ok",
        "data" : {
            "username" : user.username,
            "email" : user.email,
            "verified" : user.is_verified,
            "joined_date" : user.join_date.strftime("%b %d %Y"),
            "logo" : logo_path
        }
    }
    
    

@post_save(User)
async def create_festival(
    sender: "Type[User]",
    instance: User,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str]
) -> None:
    
    if created:
        festival_obj = await Festival.create(
            festival_name = instance.username, owner = instance
        )
        await festival_pydantic.from_tortoise_orm(festival_obj)
        #send the email
        await send_email([instance.email], instance)



@app.post('/registration')
async def user_registrations(user: user_pydanticIn):
    user_info = user.dict(exclude_unset = True)
    user_info['password'] = get_password_hash(user_info['password'])
    user_obj = await User.create(**user_info)
    new_user = await user_pydantic.from_tortoise_orm(user_obj)
    return{
        "status" : "ok",
        "data" : f"Hello {new_user.username}, Welcome"
    }


#Templates for email verification
templates = Jinja2Templates(directory="templates")
@app.get('/verification', response_class=HTMLResponse)
async def email_verification(request: Request, token: str):
    user = await very_token(token)
    
    if user and not user.is_verified:
        user.is_verified = True
        await user.save()
        return templates.TemplateResponse("verification.html", { "request": request, "username" : user.username } )
    raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid token or expired token",
            headers = {"WWW-Authenticate": "Bearer"},
        )



@app.post("/uploadfile/profile")
async def create_upload_file(file: UploadFile = File(...), 
                            user: user_pydantic = Depends(get_current_user)):
    FILEPATH = "./static/images/"
    filename = file.filename
    # test.png > ["test", "png"]
    extension = filename.split(".")[1]
    
    if extension not in ["png", "jpg"]:
        return { "status" : "error", "detail" : "File extension not allowed" }
    
    # /static/images/uR4566gkgk.png
    token_name = secrets.token_hex(10) + "." + extension
    generated_name = FILEPATH + token_name
    file_content = await file.read()
    
    with open(generated_name, "wb") as file:
        file.write(file_content)
        
    # PILLOW
    img = Image.open(generated_name)
    img = img.resize(size = (200, 200))
    img.save(generated_name)
    
    file.close()
    
    festival = await Festival.get(owner = user)
    owner = await festival.owner
    
    if owner == user:
        festival.logo = token_name
        await festival.save()
    else: 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Not authenticated to perform this action",
            headers = {"WWW-Authenticate": "Bearer"},
        )
    file_url = "localhost:8000" + generated_name[1:]
    return { "status" : "ok", "filename" : file_url }   
    
    
    
    
@app.post("/uploadfile/artist/{id}")
async def create_upload_file(id: int, file: UploadFile = File(...), 
                             user: user_pydantic = Depends(get_current_user)):
    FILEPATH = "./static/images/"
    filename = file.filename
    # test.png > ["test", "png"]
    extension = filename.split(".")[1]
    
    if extension not in ["png", "jpg"]:
        return { "status" : "error", "detail" : "File extension not allowed" }
    
    # /static/images/uR4566gkgk.png
    token_name = secrets.token_hex(10) + "." + extension
    generated_name = FILEPATH + token_name
    file_content = await file.read()
    
    with open(generated_name, "wb") as file:
        file.write(file_content)
        
    # PILLOW
    img = Image.open(generated_name)
    img = img.resize(size = (200, 200))
    img.save(generated_name)
    
    file.close()
    
    artist = await Artist.get(id = id)
    festival = await artist.festival
    owner = await festival.owner
    
    if owner == user:
        artist.artist_image = token_name
        await artist.save()
    else :
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Not authenticated to perform this action",
            headers = {"WWW-Authenticate": "Bearer"},
        )
    file_url = "localhost:8000" + generated_name[1:]
    return { "status" : "ok", "filename": file_url }



#CRUD functionality

@app.post("/artists")
async def add_new_artist(artist: artist_pydanticIn,
                        user: user_pydantic = Depends(get_current_user)):
    artist = artist.dict(exclude_unset=True)
    
    artist_obj = await Artist.create(**artist, festival = user)
    artist_obj = await artist_pydantic.from_tortoise_orm(artist_obj)
        
    return { "status" : "ok" , "data" : artist_obj }


@app.get("/artists")
async def get_artist():
    response = await artist_pydantic.from_queryset(Artist.all())
    return { "status" : "ok", "data" : response }



@app.get("/artists/{id}")
async def get_artistById(id: int):
    artist = await Artist.get(id = id)
    festival = await artist.festival
    owner = await festival.owner
    response = await artist_pydantic.from_queryset_single(Artist.get(id = id))
    return { 
            "status" : "ok", 
            "data" : {
                "artist_details" : response,
                "festival_details" : {
                    "name" : festival.festival_name,
                    "city" : festival.city,
                    "region" : festival.region,
                    "description" : festival.festival_description,
                    "logo" : festival.logo,
                    "festival_id" : festival.id,
                    "owner_id" : owner.id,
                    "email" : owner.email,
                    "join_date" : owner.join_date.strftime("%b %d %Y")
                } 
            } 
        }



@app.delete("/artists/{id}")
async def delete_artist(id : int, user: user_pydantic = Depends(get_current_user)):
    artist = await Artist.get(id = id)
    festival = await artist.festival
    owner = await festival.owner
    
    if user == owner:
        artist.delete()
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Not authenticated to perform this action",
            headers = {"WWW-Authenticate": "Bearer"},
        )
    return { "status" : "ok" }



@app.put("/artists/{id}")
async def update_artist(id: int,
                        update_info: artist_pydanticIn,
                        user: user_pydantic = Depends(get_current_user)
                    ):
    artist = await Artist.get(id = id)
    festival = await artist.festival
    owner = await festival.owner
    
    update_info = update_info.dict(exclude_unset = True)
    
    if user == owner:
        artist = await artist.update_from_dict(update_info)
        await artist.save()
        response = await artist_pydantic.from_tortoise_orm(artist)
        return { "status" : "ok", "data" : response }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Not authenticated to perform this action or invalid user input",
            headers = {"WWW-Authenticate": "Bearer"},
        )


@app.put("/festival/{id}")
async def update_festival(id: int,
                          update_festival: festival_pydanticIn,
                          user: user_pydantic = Depends(get_current_user)                          
                          ):
    update_festival = update_festival.dict()

    festival = await Festival.get(id = id)
    festival_owner = await festival.owner
    
    if user == festival_owner:
        await festival.update_from_dict(update_festival)
        festival.save()
        response = await festival_pydantic.from_tortoise_orm(festival)
        return { "status" : "ok", "data" : response}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Not authenticated to perform this action",
            headers = {"WWW-Authenticate": "Bearer"},
        )





register_tortoise(
    app,
    db_url="sqlite://database.sqlite3",
    modules={"models" : ["models"]},
    generate_schemas=True,
    add_exception_handlers=True
)

