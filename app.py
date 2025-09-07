from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_hashtags import get_hashtags  # <- use the wrapper we just added

app = Flask(__name__)
CORS(app)  # Allow frontend to call this API

@app.route("/api/hashtags", methods=["GET"])
def api_hashtags():
    query = (request.args.get("query") or "").strip()
    if not query:
        return jsonify({"error": "No query provided"}), 400
    try:
        tags = get_hashtags(query)
        return jsonify({"hashtags": tags})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
