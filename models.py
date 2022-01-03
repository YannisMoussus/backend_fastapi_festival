import pydantic
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise import Model, fields
from pydantic import BaseModel
from datetime import datetime



class User(Model):
    id = fields.IntField(pk = True, index = True)
    username = fields.CharField(max_length =20, null = False, unique = True)
    email = fields.CharField(max_length =200, null = False, unique = True)
    password = fields.CharField(max_length = 100, null = False)
    is_verified = fields.BooleanField(default = False)
    join_date = fields.DatetimeField(default = datetime.utcnow)
    


class Festival(Model):
    id = fields.IntField(pk = True, index = True)
    festival_name = fields.CharField(max_length =200, null = False, unique = True)
    city = fields.CharField(max_length =100, null = False, default = "Unspecified")
    region = fields.CharField(max_length =100, null = False, default = "Unspecified")
    festival_description = fields.TextField(null = True)
    logo = fields.CharField(max_length =200, null = False, default = "default.jpg")
    owner = fields.ForeignKeyField("models.User", related_name ="festival")
    
    

class Artist(Model):
    id = fields.IntField(pk = True, index = True)
    name = fields.CharField(max_length = 100, null = False, index = True)
    category = fields.CharField(max_length =30, index = True)
    age = fields.CharField(max_length=10, index = True)
    artist_image = fields.CharField(max_length =200, null = False, default = "artistDefault.jpg")
    festival = fields.ForeignKeyField("models.Festival", related_name="artists")
    
    

user_pydantic = pydantic_model_creator(User, name = "User", exclude=("is_verified" , ))
user_pydanticIn = pydantic_model_creator(User, name = "UserIn", exclude_readonly=True, exclude=("is_verified" , "join_date"))
user_pydanticOut = pydantic_model_creator(User, name = "UserOut", exclude=("password", ))



festival_pydantic = pydantic_model_creator(Festival, name = "Festival")
festival_pydanticIn = pydantic_model_creator(Festival , name = "FestivalIn", exclude=("logo", "id"))



artist_pydantic = pydantic_model_creator(Artist, name="Artist")
artist_pydanticIn = pydantic_model_creator(Artist, name="ArtistIn", exclude=("id", "artist_image")) 