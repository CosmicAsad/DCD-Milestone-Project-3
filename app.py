# Configuration code
import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


# Route for home page, displays all games from database
@app.route("/")
@app.route("/all_games")
def all_games():
    games = list(mongo.db.games.find().sort("game_name"))
    print(games)
    reviews = list(mongo.db.reviews.find())
    print(reviews)
    return render_template("games.html", games=games, reviews=reviews)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    games = list(mongo.db.games.find({"$text": {"$search": query}}))
    return render_template("games.html", games=games)


# Route for register page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Checks for existing usernames
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # Put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration successful!")
        return redirect(url_for("profile", username=session["user"]))
    return render_template("register.html")


# Route for login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Check if username exists
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
               existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(
                    request.form.get("username")))
                return redirect(url_for(
                    "profile", username=session["user"]))
            else:
                # Invalid password
                flash("Username and/or Password is incorrect")
                return redirect(url_for("login"))

        else:
            # Username doesn't exist
            flash("Username and/or Password is incorrect")
            return redirect(url_for("login"))
    return render_template("login.html")


# Displays Profile page and username in URL
@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # Retrieve username from MongoDB
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


# Route for logout link
@app.route("/logout")
def logout():
    # Remove user from session cookies
    flash("You have been logged out.")
    session.pop("user")
    return redirect(url_for("login"))


# Route for add review page
@app.route("/add_review/<game_id>", methods=["GET", "POST"])
def add_review(game_id):
    if request.method == "POST":
        review = {
            "review": request.form.get("review"),
            "created_by": session["user"],
            "game_id": ObjectId(game_id),
        }
        mongo.db.reviews.insert_one(review)
        flash("Review Added Successfully")
        return redirect(url_for("all_games"))

    game = mongo.db.games.find_one({"_id": ObjectId(game_id)})
    return render_template("add_review.html", game=game)


# Route for edit review page
@app.route("/edit_review/<review_id>", methods=["GET", "POST"])
def edit_review(review_id):
    if request.method == "POST":
        review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
        game_id = review["game_id"]
        edited = {
            "review": request.form.get("review"),
            "created_by": session["user"],
            "game_id": ObjectId(game_id),
        }
        mongo.db.reviews.update({"_id": ObjectId(review_id)}, edited)
        flash("Review Edited Successfully")
        return redirect(url_for("all_games"))
    review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
    game = mongo.db.games.find().sort("game_name")
    return render_template("edit_review.html", review=review, game=game)


# Route to delete review
@app.route("/delete_review/<review_id>")
def delete_review(review_id):
    mongo.db.reviews.remove({"_id": ObjectId(review_id)})
    flash("Review Deleted")
    return redirect(url_for("all_games"))


# Route for Admin to manage games
@app.route("/manage_games")
def manage_games():
    games = list(mongo.db.games.find().sort("game_name"))
    return render_template("manage_games.html", games=games)


# Route for Admin to add games
@app.route("/add_game", methods=["GET", "POST"])
def add_game():
    if request.method == "POST":
        game = {
            "game_name": request.form.get("game_name"),
            "game_genre": request.form.get("game_genre"),
            "game_description": request.form.get("game_description"),
            "game_img": request.form.get("game_img"),
        }
        mongo.db.games.insert_one(game)
        flash("New Game Added")
        return redirect(url_for("manage_games"))

    return render_template("add_game.html")


# Edit games functionality
@app.route("/edit_game/<game_id>", methods=["GET", "POST"])
def edit_game(game_id):
    if request.method == "POST":
        submit = {
            "game_name": request.form.get("game_name"),
            "game_genre": request.form.get("game_genre"),
            "game_description": request.form.get("game_description"),
            "game_img": request.form.get("game_img"),
        }
        mongo.db.games.update({"_id": ObjectId(game_id)}, submit)
        flash("Game Updated")
        return redirect(url_for("manage_games"))
    game = mongo.db.games.find_one({"_id": ObjectId(game_id)})
    return render_template("edit_game.html", game=game)


# Delete games functionality
@app.route("/delete_game/<game_id>")
def delete_game(game_id):
    mongo.db.games.remove({"_id": ObjectId(game_id)})
    flash("Game Deleted")
    return redirect(url_for("manage_games"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)
