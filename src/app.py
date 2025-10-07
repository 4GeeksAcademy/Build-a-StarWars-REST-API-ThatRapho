import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Character, Planet, Favorite
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.serialize() for user in users]), 200


@app.route('/users/favorites', methods=['GET'])
def get_user_favorites():
    user = User.query.get(1)
    if not user:
        return jsonify({"error": "User not found"}), 404
    favorites = Favorite.query.filter_by(user_id=user.id).all()
    return jsonify([f.serialize() for f in favorites]), 200

@app.route('/planets', methods=['POST'])
def add_planet():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "Missing planet name"}), 400

    planet = Planet(
        name=data.get("name"),
        climate=data.get("climate"),
        terrain=data.get("terrain"),
        population=data.get("population")
    )
    db.session.add(planet)
    db.session.commit()
    return jsonify({"message": "Planet created", "planet": planet.serialize()}), 201

@app.route('/people', methods=['POST'])
def add_person():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "Missing character name"}), 400

    try:
        person = Character(
            name=data.get("name"),
            gender=data.get("gender", ""),
            birth_year=data.get("birth_year", ""),
            eye_color=data.get("eye_color", "")
        )
        db.session.add(person)
        db.session.commit()
        return jsonify({"message": "Character created", "character": person.serialize()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Could not create character", "details": str(e)}), 500

@app.route('/people', methods=['GET'])
def get_all_people():
    people = Character.query.all()
    return jsonify([p.serialize() for p in people]), 200


@app.route('/people/<int:people_id>', methods=['GET'])
def get_person(people_id):
    person = Character.query.get(people_id)
    if not person:
        return jsonify({"error": "Character not found"}), 404
    return jsonify(person.serialize()), 200


@app.route('/planets', methods=['GET'])
def get_all_planets():
    planets = Planet.query.all()
    return jsonify([p.serialize() for p in planets]), 200


@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"error": "Planet not found"}), 404
    return jsonify(planet.serialize()), 200


@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    user = User.query.get(1)
    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"error": "Planet not found"}), 404

    favorite = Favorite(user_id=user.id, planet_id=planet.id)
    db.session.add(favorite)
    db.session.commit()
    return jsonify({"message": f"Planet {planet.name} added to favorites"}), 201


@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_person(people_id):
    user = User.query.get(1)
    person = Character.query.get(people_id)
    if not person:
        return jsonify({"error": "Character not found"}), 404

    favorite = Favorite(user_id=user.id, character_id=person.id)
    db.session.add(favorite)
    db.session.commit()
    return jsonify({"message": f"Character {person.name} added to favorites"}), 201


@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    user_id = 1  # default for testing until you implement auth
    favorite = Favorite.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    if not favorite:
        return jsonify({"error": f"Favorite planet with id {planet_id} not found"}), 404

    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"message": f"Favorite planet {planet_id} deleted"}), 200


@app.route('/favorite/people/<int:character_id>', methods=['DELETE'])
def delete_favorite_person(character_id):
    user_id = 1  # current test user
    favorite = Favorite.query.filter_by(user_id=user_id, character_id=character_id).first()
    if not favorite:
        return jsonify({"error": f"Favorite for character {character_id} not found"}), 404

    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"message": f"Favorite for character {character_id} deleted"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
