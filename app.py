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

DATABASE_URL = os.getenv("DATABASE_URL")
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
wealth,
multimillionaire_level,
status,
personal_tech_level,
point_value,
available_points
"""

APPEARANCE_JOIN = "appearance on appearance.character_fk = character.id"
APPEARANCE_COLUMNS = """
appearance.id as appearance_id,
appearance.appearance as appearance_appearance,
appearance.description as appearance_description,
appearance.androgynous as appearance_androgynous,
appearance.impressive as appearance_impressive,
appearance.universal as appearance_universal,
appearance.off_the_shelf_looks as appearance_off_the_shelf_looks
"""

LANGUAGE_JOIN = "language on language.character_fk = character.id"
LANGUAGE_COLUMNS = """
language.id as language_id,
language.name as language_name,
language.spoken_comprehension as language_spoken_comprehension,
language.written_comprehension as language_written_comprehension
"""

REPUTATION_JOIN = "reputation on reputation.character_fk = character.id"
REPUTATION_COLUMNS = """
reputation.id as reputation_id,
reputation.description as reputation_description,
reputation.reaction as reputation_reaction,
reputation.scope as reputation_scope,
reputation.group as reputation_group,
reputation.frequency as reputation_frequency,
reputation.free as reputation_free
"""

RANK_JOIN = "rank on rank.character_fk = character.id"
RANK_COLUMNS = """
rank.id as rank_id,
rank.organization as rank_organization,
rank.rank as rank_rank,
rank.description as rank_description,
rank.replaces_status as rank_replaces_status
"""

# SQL Queries
SELECT_ALL_CHARACTERS = """
select 
    {CHARACTER_COLUMNS},
    {APPEARANCE_COLUMNS},
    {LANGUAGE_COLUMNS},
    {REPUTATION_COLUMNS},
    {RANK_COLUMNS}
from character
join {APPEARANCE_JOIN}
join {LANGUAGE_JOIN}
join {REPUTATION_JOIN}
join {RANK_JOIN}
""".format(
    CHARACTER_COLUMNS = CHARACTER_COLUMNS,
    APPEARANCE_COLUMNS = APPEARANCE_COLUMNS,
    LANGUAGE_COLUMNS = LANGUAGE_COLUMNS,
    REPUTATION_COLUMNS = REPUTATION_COLUMNS,
    RANK_COLUMNS = RANK_COLUMNS,
    APPEARANCE_JOIN = APPEARANCE_JOIN,
    LANGUAGE_JOIN = LANGUAGE_JOIN,
    REPUTATION_JOIN = REPUTATION_JOIN,
    RANK_JOIN = RANK_JOIN)
SELECT_CHARACTER_BY_ID = SELECT_ALL_CHARACTERS + """ where character.id=%s"""

try:
    if DATABASE_URL != "":
        conn = psycopg2.connect(DATABASE_URL)
        print("Test")
    else:
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, dbname=DB_NAME)
except:
    print("I am unable to connect to the database.")

cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

def appendIfNotPresent(list, append):
    if append['id']:
        if list:
            exists = False
            for item in list:
                if item['id'] == append['id']:
                    exists = True
                    break
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
    character['wealth'] = d.get('wealth')
    character['multimillionaireLevel'] = d.get('multimillionaire_level')
    character['status'] = d.get('status')
    character['personalTechLevel'] = d.get('personal_tech_level')
    character['pointValue'] = d.get('point_value')
    character['availablePoints'] = d.get('available_points')
    character['appearance'] = {
        "id": d.get('appearance_id'),
        "appearance": d.get('appearance_appearance'),
        "description": d.get('appearance_description'),
        "androgynous": d.get('appearance_androgynous'),
        "impressive": d.get('appearance_impressive'),
        "universal": d.get('appearance_universal'),
        "offTheShelfLooks": d.get('appearance_off_the_shelf_looks')
    }
    character['languages'] = []
    character['reputations'] = []
    character['ranks'] = []
    for c in characterData:
        language = {
            "id": c.get('language_id'),
            "name": c.get('language_name'),
            "spokenComprehension": c.get('language_spoken_comprehension'),
            "writtenComprehension": c.get('language_written_comprehension')
        }
        character['languages'] = appendIfNotPresent(character['languages'], language)

        reputation = {
            "id": c.get('reputation_id'),
            "description": c.get('reputation_description'),
            "reaction": c.get('reputation_reaction'),
            "scope": c.get('reputation_scope'),
            "group": c.get('reputation_group'),
            "frequency": c.get('reputation_frequency'),
            "free": c.get('reputation_free')
        }
        character['reputations'] = appendIfNotPresent(character['reputations'], reputation)

        rank = {
            "id": c.get('rank_id'),
            "organization": c.get('rank_organization'),
            "rank": c.get('rank_rank'),
            "description": c.get('rank_description'),
            "replacesStatus": c.get('rank_replaces_status')
        }
        character['ranks'] = appendIfNotPresent(character['ranks'], rank)
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