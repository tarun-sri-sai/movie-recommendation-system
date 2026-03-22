from flask import Blueprint, request, jsonify
from src.recommender import Recommender
from src.utils import validate_input

v1_bp = Blueprint("v1", __name__, url_prefix="/api/v1")
recommender = Recommender()


@v1_bp.route("/recommend", methods=["POST"])
def recommend():
    try:
        try:
            user_ratings = request.get_json(force=True)
        except Exception as e:
            return (
                jsonify({"error": f"Invalid JSON in request body: {str(e)}"}),
                400
            )

        is_valid, error_msg = validate_input(user_ratings)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        recommendations = recommender.get_recommendations(user_ratings)

        return jsonify(recommendations), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            500
        )


@v1_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"version": "v1"}), 200
