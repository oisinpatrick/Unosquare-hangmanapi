import uuid
import random

from flask import (Blueprint, abort, jsonify, request)
from werkzeug.exceptions import HTTPException

mod = Blueprint('games', __name__, url_prefix='/games')

games = {}

word_list = ["Banana", "Canine", "Unosquare", "Airport"]

def generate_word():
    return random.choice(word_list)

def mask_word(word, correct_guesses):
    word_lower = word.lower()
    # Initialize an empty string for the masked word
    masked_word = ""
    # Iterate over each letter in the lowercase word
    for letter in word_lower:
        if letter in correct_guesses:
            # If the letter has been correctly guessed, add it to the masked word
            masked_word += word[word_lower.index(letter)]
        else:
            masked_word += "_"
    return masked_word.strip()

def is_valid_guess(guess, game):
    if not guess.isalpha() or len(guess) != 1:
        return False
    return True

@mod.route('/', methods=['POST'])
def start_game():
    game_id = str(uuid.uuid4())
    word = generate_word()
    games[game_id] = {
        "word": word,
        "guessed_letters": [],
        "correct_guesses": [],
        "attempts": 6,
    }
    return game_id, 201

@mod.route('/<string:game_id>', methods=['GET'])
def get_game_state(game_id):
    game = games.get(game_id)
    if game is None:
        abort(404)
    masked_word = mask_word(game["word"], game["correct_guesses"])
    
    # Return statement for GET method when game has been lost
    if game["attempts"] == 0:
        return jsonify({
            "word": game["word"],
            "incorrect_guesses": game["guessed_letters"],
            "remaining_attempts": game["attempts"],
            "status": "Loss"
        })
    
    # Return statement for GET method when game has been won
    if "_" not in masked_word and game["attempts"] > 0:
        return jsonify({
            "word": masked_word,
            "incorrect_guesses": game["guessed_letters"],
            "remaining_attempts": game["attempts"],
            "status": "Won"
        })
    
    # Return statement for GET method when the game is still in progress
    return jsonify({
        "incorrect_guesses": game["guessed_letters"],
        "remaining_attempts": game["attempts"],
        "status": "In Progress",
        "word": masked_word 
    })

@mod.route('/<string:game_id>/guesses', methods=['POST'])
def make_guess(game_id):
    game = games.get(game_id)
    if game is None:
        abort(404)
    if not request.json or 'letter' not in request.json:
        abort(400)
    guess = request.json['letter']
    if not is_valid_guess(guess, game):
        return jsonify({"Message": "Guess must be supplied with 1 letter"}), 400

    guess = guess.lower()
    masked_word = mask_word(game["word"], game["correct_guesses"])

    if guess in game["guessed_letters"] or guess in game["correct_guesses"]:
        # If the same letter has already been guessed, return an error message
        return "ERROR: Cannot guess the same letter twice!"

    if guess in game["word"].lower():
        # If the guess is correct, add it to the correct guesses and update the masked word
        game["correct_guesses"].append(guess)
        masked_word = mask_word(game["word"], game["correct_guesses"])

    if guess not in game["word"].lower():
        # If the guess is incorrect, add it to the guessed letters and decrease the attempts
        game["guessed_letters"].append(guess)
        game["attempts"] -= 1

    if game["attempts"] <= 0:
        # If there are no attempts remaining, return a message indicating loss
        return jsonify({
            "message": "You lost!",
            "word": game["word"]
        }), 400

    if "_" not in masked_word and game["attempts"] > 0:
        # If there are no underscores in the masked word and attempts are remaining, the player has won
        return jsonify({
            "message": "You won!",
            "word": masked_word
        }), 400

    # Return the game state with the incorrect guesses, remaining attempts, status, and masked word
    return jsonify({
        "incorrect_guesses": game["guessed_letters"],
        "remaining_attempts": game["attempts"],
        "status": "In Progress",
        "word": masked_word
    })


