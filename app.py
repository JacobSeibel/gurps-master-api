from typing import Dict
from flask import Flask, request
from flask_cors import CORS, cross_origin
import os
import psycopg2
import psycopg2.extras
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy.sql.expression import insert, select, update
from sqlalchemy.sql.schema import MetaData, Table

app = Flask(__name__)
cors = CORS(app)

load_dotenv()

# Replace postgres with postgresql so sqlalchemy doesn't complain
DATABASE_URL = os.getenv("DATABASE_URL").replace('postgres://', 'postgresql://', 1)

engine = create_engine(DATABASE_URL)
meta = MetaData(engine)
characterTable = Table('character', meta, autoload=True)
appearanceTable = Table('appearance', meta, autoload=True)
languageTable = Table('language', meta, autoload=True)
reputationTable = Table('reputation', meta, autoload=True)
rankTable = Table('rank', meta, autoload=True)
characterJoin = (
    characterTable.
    join(appearanceTable, isouter=True).
    join(languageTable, isouter=True).
    join(reputationTable, isouter=True).
    join(rankTable, isouter=True)
)

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
    character['id'] = d.id
    character['name'] = d.name
    character['player'] = d.player
    character['height'] = d.height
    character['weight'] = d.weight
    character['build'] = d.build
    character['size'] = d.size
    character['st'] = d.st
    character['dx'] = d.dx
    character['iq'] = d.iq
    character['ht'] = d.ht
    character['basicSpeed'] = d.basic_speed
    character['hp'] = d.hp
    character['will'] = d.will
    character['per'] = d.per
    character['fp'] = d.fp
    character['wealth'] = d.wealth
    character['multimillionaireLevel'] = d.multimillionaire_level
    character['status'] = d.status
    character['personalTechLevel'] = d.personal_tech_level
    character['pointValue'] = d.point_value
    character['availablePoints'] = d.available_points
    character['appearance'] = {
        "id": d.appearance_id,
        "appearance": d.appearance_appearance,
        "description": d.appearance_description,
        "androgynous": d.appearance_androgynous,
        "impressive": d.appearance_impressive,
        "universal": d.appearance_universal,
        "offTheShelfLooks": d.appearance_off_the_shelf_looks
    }
    character['languages'] = []
    character['reputations'] = []
    character['ranks'] = []
    for c in characterData:
        language = {
            "id": c.language_id,
            "name": c.language_name,
            "spokenComprehension": c.language_spoken_comprehension,
            "writtenComprehension": c.language_written_comprehension
        }
        character['languages'] = appendIfNotPresent(character['languages'], language)

        reputation = {
            "id": c.reputation_id,
            "description": c.reputation_description,
            "reaction": c.reputation_reaction,
            "scope": c.reputation_scope,
            "group": c.reputation_group,
            "frequency": c.reputation_frequency,
            "free": c.reputation_free
        }
        character['reputations'] = appendIfNotPresent(character['reputations'], reputation)

        rank = {
            "id": c.rank_id,
            "organization": c.rank_organization,
            "rank": c.rank_rank,
            "description": c.rank_description,
            "replacesStatus": c.rank_replaces_status
        }
        character['ranks'] = appendIfNotPresent(character['ranks'], rank)
    return character

@cross_origin()
@app.route('/character')
def allCharacters():
    rs = None
    try:
        stm = (
            select(
                [
                    characterTable,
                    appearanceTable,
                    languageTable,
                    reputationTable,
                    rankTable
                ]
            ).
            select_from(characterJoin)
        )
        rs = engine.connect().execute(stm)
    except:
        print("Can't select from character")

    rows = rs.fetchall()
    characterRows = dict()
    for row in rows:
        if row['id'] in characterRows.keys():
            characterRows[row['id']].append(row)
        else:
            characterRows[row['id']] = [row]
    characters = []
    for key in characterRows.keys():
        characters.append(buildCharacter(characterRows[key]))
    return {"characters": characters}

@cross_origin()
@app.route('/character/<id>')
def character(id):
    try:
        stm = (
            select(
                [
                    characterTable,
                    appearanceTable,
                    languageTable,
                    reputationTable,
                    rankTable
                ]
            ).
            select_from(characterJoin).
            where(characterTable.c.id == id)
        )
        rs = engine.connect().execute(stm)
    except:
        print("Can't select from character")

    return buildCharacter(rs.fetchall())

@cross_origin()
@app.route('/character', methods=['PUT'])
def updateCharacter():
    character = request.json
    try:
        stm = (
            update(appearanceTable).
            where(appearanceTable.c.character_fk == character["id"]).
            values(
                {
                    "appearance": character["appearance"]["appearance"],
                    "description": character["appearance"]["description"],
                    "androgynous": character["appearance"]["androgynous"],
                    "impressive": character["appearance"]["impressive"],
                    "universal": character["appearance"]["universal"],
                    "off_the_shelf_looks": character["appearance"]["offTheShelfLooks"]
                }
            )
        )
        engine.connect().execute(stm)
    except:
        print("Failed to update appearance")

    # process languages
    try:
        stm = (
            select(languageTable).
            where(languageTable.c.character_fk == character["id"])
        )
        rs = engine.connect().execute(stm)
    except:
        print("Failed to fetch existing language ids for character")
    languageIds = rs.fetchall()
    insertLanguages = []
    updateLanguages = []
    deleteLanguages = []
    for language in character["languages"]:
        if language["id"]:
            delete = True
            for languageId in languageIds:
                if language["id"] == languageId["id"]:
                    updateLanguages.append(language)
                    delete = False
                    break
            if delete:
                deleteLanguages.append(language)
        else:
            insertLanguages.append(language)

    # insert new languages
    for language in insertLanguages:
        try:
            stm = (
                insert(languageTable).
                values(
                    {
                        "character_fk": character["id"],
                        "name": language["name"],
                        "spoken_comprehension": language["spokenComprehension"],
                        "written_comprehension": language["writtenComprehension"]
                    }
                )
            )
            engine.connect().execute(stm)
        except:
            print("Failed to insert new language")

    # update old languages
    for language in updateLanguages:
        try:
            stm = (
                update(languageTable).
                where(languageTable.c.id == language["id"]).
                values(
                    {
                        "name": language["name"],
                        "spoken_comprehension": language["spokenComprehension"],
                        "written_comprehension": language["writtenComprehension"]
                    }
                )
            )
            engine.connect().execute(stm)
        except:
            print("Failed to update language")

    # delete deleted languages
    for language in deleteLanguages:
        try:
            stm = (
                delete(languageTable).
                where(languageTable.c.id == language["id"])
            )
            engine.connect().execute(stm)
        except:
            print("Failed to delete language")

    # process ranks
    try:
        stm = (
            select(rankTable).
            where(rankTable.c.character_fk == character["id"])
        )
        rs = engine.connect().execute(stm)
    except:
        print("Failed to fetch existing rank ids for character")
    rankIds = rs.fetchall()
    insertRanks = []
    updateRanks = []
    deleteRanks = []
    for rank in character["ranks"]:
        if rank["id"]:
            delete = True
            for rankId in rankIds:
                if rank["id"] == rankId["id"]:
                    updateRanks.append(rank)
                    delete = False
                    break
            if delete:
                deleteRanks.append(rank)
        else:
            insertRanks.append(rank)

    # insert new ranks
    for rank in insertRanks:
        try:
            stm = (
                insert(rankTable).
                values(
                    {
                        "organization": rank["organization"],
                        "rank": rank["rank"],
                        "description": rank["description"],
                        "replaces_status": rank["replacesStatus"],
                        "character_fk": character["id"]
                    }
                )
            )
            engine.connect().execute(stm)
        except:
            print("Failed to insert new rank")

    # update old ranks
    for rank in updateRanks:
        try:
            stm = (
                update(rankTable).
                where(rankTable.c.id == rank["id"]).
                values(
                    {
                        "organization": rank["organization"],
                        "rank": rank["rank"],
                        "description": rank["description"],
                        "replaces_status": rank["replacesStatus"]
                    }
                )
            )
            engine.connect().execute(stm)
        except:
            print("Failed to update rank")

    # delete deleted ranks
    for rank in deleteRanks:
        try:
            stm = (
                delete(rankTable).
                where(rankTable.c.id == rank["id"])
            )
            engine.connect().execute(stm)
        except:
            print("Failed to delete rank")

    # process reputations
    try:
        stm = (
            select(reputationTable).
            where(reputationTable.c.character_fk == character["id"])
        )
        rs = engine.connect().execute(stm)
    except:
        print("Failed to fetch existing reputation ids for character")
    reputationIds = rs.fetchall()
    insertReputations = []
    updateReputations = []
    deleteReputations = []
    for reputation in character["reputations"]:
        if reputation["id"]:
            delete = True
            for reputationId in reputationIds:
                if reputation["id"] == reputationId["id"]:
                    updateReputations.append(reputation)
                    delete = False
                    break
            if delete:
                deleteReputations.append(reputation)
        else:
            insertReputations.append(reputation)

    # insert new reputations
    for reputation in insertReputations:
        try:
            stm = (
                insert(reputationTable).
                values(
                    {
                        "description": reputation["description"],
                        "reaction": reputation["reaction"],
                        "scope": reputation["scope"],
                        "group": reputation["group"],
                        "frequency": reputation["frequency"],
                        "free": reputation["free"],
                        "character_fk": character["id"]
                    }
                )
            )
            engine.connect().execute(stm)
        except:
            print("Failed to insert new reputation")

    # update old reputations
    for reputation in updateReputations:
        try:
            stm = (
                update(reputationTable).
                where(reputationTable.c.id == reputation["id"]).
                values(
                    {
                        "description": reputation["description"],
                        "reaction": reputation["reaction"],
                        "scope": reputation["scope"],
                        "group": reputation["group"],
                        "frequency": reputation["frequency"],
                        "free": reputation["free"]
                    }
                )
            )
            engine.connect().execute(stm)
        except:
            print("Failed to update reputation")

    # delete deleted reputations
    for reputation in deleteReputations:
        try:
            stm = (
                delete(reputationTable).
                where(reputationTable.c.id == reputation["id"])
            )
            engine.connect().execute(stm)
        except:
            print("Failed to delete reputation")

    # update character
    try:
        stm = (
            update(characterTable).
            where(characterTable.c.id == character["id"]).
            values(
                {
                    "name": character["name"],
                    "player": character["player"],
                    "height": character["height"],
                    "weight": character["weight"],
                    "build": character["build"],
                    "size": character["size"],
                    "st": character["st"],
                    "dx": character["dx"],
                    "iq": character["iq"],
                    "ht": character["ht"],
                    "basic_speed": character["basicSpeed"],
                    "hp": character["hp"],
                    "will": character["will"],
                    "per": character["per"],
                    "fp": character["fp"],
                    "wealth": character["wealth"],
                    "multimillionaire_level": character["multimillionaireLevel"],
                    "status": character["status"],
                    "personal_tech_level": character["personalTechLevel"],
                    "point_value": character["pointValue"],
                    "available_points": character["availablePoints"]
                }
            )
        )
        engine.connect().execute(stm)
    except:
        print("Failed to update character")
    
    return {"Message": "Successfully updated character!"}

@cross_origin()
@app.route('/character', methods=['POST'])
def insertCharacter():
    character = request.json
    # insert the character entry
    try:
        stm = (
            insert(characterTable).
            values(
                {
                    "name": character["name"],
                    "player": character["player"],
                    "height": character["height"],
                    "weight": character["weight"],
                    "build": character["build"],
                    "size": character["size"],
                    "st": character["st"],
                    "dx": character["dx"],
                    "iq": character["iq"],
                    "ht": character["ht"],
                    "basic_speed": character["basicSpeed"],
                    "hp": character["hp"],
                    "will": character["will"],
                    "per": character["per"],
                    "fp": character["fp"],
                    "wealth": character["wealth"],
                    "multimillionaire_level": character["multimillionaireLevel"],
                    "status": character["status"],
                    "personal_tech_level": character["personalTechLevel"],
                    "point_value": character["pointValue"],
                    "available_points": character["availablePoints"]
                }
            ).returning(
                characterTable.c.id
            )
        )
        rs = engine.connect().execute(stm)
    except:
        print("Failed to insert character")

    character["id"] = rs.fetchone()["id"]
    
    # insert the appearance entry
    try:
        stm = (
            insert(appearanceTable).
            values(
                {
                    "appearance": character["appearance"]["appearance"],
                    "description": character["appearance"]["description"],
                    "androgynous": character["appearance"]["androgynous"],
                    "impressive": character["appearance"]["impressive"],
                    "universal": character["appearance"]["universal"],
                    "off_the_shelf_looks": character["appearance"]["offTheShelfLooks"],
                    "character_fk": character["id"]
                }
            )
        )
        engine.connect().execute(stm)
    except:
        print("Failed to insert appearance")

    # insert languages
    for language in character["languages"]:
        try:
            stm = (
                insert(languageTable).
                values(
                    {
                        "character_fk": character["id"],
                        "name": language["name"],
                        "spoken_comprehension": language["spokenComprehension"],
                        "written_comprehension": language["writtenComprehension"]
                    }
                )
            )
            engine.connect().execute(stm)
        except:
            print("Failed to insert new language")

    # insert ranks
    for rank in character["ranks"]:
        try:
            stm = (
                insert(rankTable).
                values(
                    {
                        "organization": rank["organization"],
                        "rank": rank["rank"],
                        "description": rank["description"],
                        "replaces_status": rank["replacesStatus"],
                        "character_fk": character["id"]
                    }
                )
            )
            engine.connect().execute(stm)
        except:
            print("Failed to insert new rank")

    # insert reputations
    for reputation in character["reputations"]:
        try:
            stm = (
                insert(reputationTable).
                values(
                    {
                        "description": reputation["description"],
                        "reaction": reputation["reaction"],
                        "scope": reputation["scope"],
                        "group": reputation["group"],
                        "frequency": reputation["frequency"],
                        "free": reputation["free"],
                        "character_fk": character["id"]
                    }
                )
            )
            engine.connect().execute(stm)
        except:
            print("Failed to insert new reputation")
    
    return {"Message": "Successfully inserted character!"}


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)