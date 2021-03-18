from typing import Dict
from flask import Flask, request
from flask_cors import CORS, cross_origin
import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

app = Flask(__name__)
cors = CORS(app)

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")

# SQL Columns
CHARACTER_COLUMNS = """
character.id,
character.name,
player,
height,
weight,
appearance_description,
appearance,
build,
size,
st,
dx,
iq,
ht,
basic_speed,
hp,
will,
per,
fp,
androgynous,
impressive,
universal,
off_the_shelf_looks,
wealth,
multimillionaire_level,
status,
personal_tech_level,
point_value,
available_points
"""

LANGUAGE_COLUMNS = """
language.id as language_id,
language.name as language_name,
spoken_comprehension,
written_comprehension
"""

# SQL Queries
SELECT_ALL_CHARACTERS = """
select 
    {CHARACTER_COLUMNS},
    {LANGUAGE_COLUMNS}
from character
join language on language.character_fk = character.id
""".format(CHARACTER_COLUMNS = CHARACTER_COLUMNS, LANGUAGE_COLUMNS = LANGUAGE_COLUMNS)
SELECT_CHARACTER_BY_ID = SELECT_ALL_CHARACTERS + """ where character.id=%s"""

try:
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, dbname=DB_NAME)
except:
    print("I am unable to connect to the database.")

cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

def appendIfNotPresent(list, append):
    if append['id']:
        if list:
            exists = False
            for item in list:
                exists = exists and (item['id'] == append['id'])
            if not exists:
                list.append(append)
                return list
        else:
            return [append]

def buildCharacter(characterData):
    character = dict()
    d: psycopg2.extras.RealDictRow = characterData[0]
    character['id'] = d.get('id')
    character['name'] = d.get('name')
    character['player'] = d.get('player')
    character['height'] = d.get('height')
    character['weight'] = d.get('weight')
    character['appearanceDescription'] = d.get('appearance_description')
    character['appearance'] = d.get('appearance')
    character['build'] = d.get('build')
    character['size'] = d.get('size')
    character['st'] = d.get('st')
    character['dx'] = d.get('dx')
    character['iq'] = d.get('iq')
    character['ht'] = d.get('ht')
    character['basicSpeed'] = d.get('basic_speed')
    character['hp'] = d.get('hp')
    character['will'] = d.get('will')
    character['per'] = d.get('per')
    character['fp'] = d.get('fp')
    character['androgynous'] = d.get('androgynous')
    character['impressive'] = d.get('impressive')
    character['universal'] = d.get('universal')
    character['offTheShelfLooks'] = d.get('off_the_shelf_looks')
    character['wealth'] = d.get('wealth')
    character['multimillionaireLevel'] = d.get('multimillionaire_level')
    character['status'] = d.get('status')
    character['personalTechLevel'] = d.get('personal_tech_level')
    character['pointValue'] = d.get('point_value')
    character['availablePoints'] = d.get('available_points')
    character['languages'] = []
    for c in characterData:
        language = {
            "id": c.get('language_id'),
            "name": c.get('language_name'),
            "spokenComprehension": c.get('spoken_comprehension'),
            "writtenComprehension": c.get('written_comprehension')
        }
        character['languages'] = appendIfNotPresent(character['languages'], language)
    return character



@cross_origin()
@app.route('/character')
@app.route('/character/<id>')
def character(id=None):
    if id:
        try:
            cur.execute(SELECT_CHARACTER_BY_ID, id)
        except:
            print("Can't select from character")

        result = cur.fetchall()
        return buildCharacter(result)
    else:
        try:
            cur.execute(SELECT_ALL_CHARACTERS)
        except:
            print("Can't select from character")

        rows = cur.fetchall()
        characterRows = dict()
        for row in rows:
            if row['id'] in characterRows.keys():
                characterRows[row['id']].append(row)
            else:
                characterRows[row['id']] = [row]
        characters = []
        for key in characterRows.keys():
            print(key)
            characters.append(buildCharacter(characterRows[key]))
        return {"characters": characters}
        

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)