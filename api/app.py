from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import random
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Store IoT interactions
iot_interactions = []

# Mock recommendation data
MOCK_MOVIES = [
    {"id": 1, "title": "Toy Story", "genres": "Animation|Children|Comedy", "rating": 4.8},
    {"id": 50, "title": "The Usual Suspects", "genres": "Crime|Mystery|Thriller", "rating": 4.7},
    {"id": 100, "title": "Fargo", "genres": "Comedy|Crime|Drama", "rating": 4.6},
    {"id": 150, "title": "Apollo 13", "genres": "Adventure|Drama", "rating": 4.5},
    {"id": 200, "title": "The Silence of the Lambs", "genres": "Crime|Horror", "rating": 4.9},
    {"id": 250, "title": "The Shawshank Redemption", "genres": "Drama", "rating": 4.8},
    {"id": 300, "title": "Forrest Gump", "genres": "Drama|Romance", "rating": 4.7},
    {"id": 350, "title": "Pulp Fiction", "genres": "Crime|Drama", "rating": 4.6}
]

@app.route('/')
def home():
    return jsonify({
        "message": "SmartFlix API Server",
        "status": "running",
        "endpoints": {
            "/api/interact": "Handle IoT interactions",
            "/api/recommend": "Get recommendations",
            "/api/status": "Get system status"
        }
    })

@app.route('/api/interact', methods=['POST'])
def handle_interaction():
    """Handle IoT device interactions"""
    try:
        data = request.get_json()
        interaction_type = data.get('type', 'unknown')
        interaction_data = data.get('data', '')
        device = data.get('device', 'unknown')
        
        # Log interaction
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'type': interaction_type,
            'data': interaction_data,
            'device': device
        }
        iot_interactions.append(interaction)
        
        print(f"📱 IoT Interaction: {interaction_type} from {device}")
        
        # Generate recommendations based on interaction type
        if interaction_type == 'voice':
            # Simulate voice command processing
            recommendations = get_recommendations(5, "voice")
            response_data = {
                "status": "success",
                "message": "Voice command processed",
                "interaction": interaction_type,
                "recommendations": recommendations
            }
        elif interaction_type == 'tilt':
            recommendations = get_recommendations(3, "tilt")
            response_data = {
                "status": "success", 
                "message": "Tilt gesture recognized",
                "interaction": interaction_type,
                "recommendations": recommendations
            }
        elif interaction_type == 'button':
            recommendations = get_recommendations(3, "button")
            response_data = {
                "status": "success",
                "message": "Button press registered",
                "interaction": interaction_type,
                "recommendations": recommendations
            }
        else:
            response_data = {
                "status": "success",
                "message": "Interaction received",
                "interaction": interaction_type
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/recommend', methods=['GET'])
def get_recommendations_api():
    """Get movie recommendations"""
    try:
        count = request.args.get('count', 3, type=int)
        user_id = request.args.get('user_id', 1, type=int)
        
        recommendations = get_recommendations(count, "api")
        
        return jsonify({
            "status": "success",
            "user_id": user_id,
            "count": len(recommendations),
            "recommendations": recommendations
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    return jsonify({
        "status": "running",
        "iot_interactions": len(iot_interactions),
        "server_time": datetime.now().isoformat(),
        "active_devices": 1
    })

def get_recommendations(count=3, source="default"):
    """Generate mock recommendations"""
    # Shuffle and return top N movies
    shuffled = MOCK_MOVIES.copy()
    random.shuffle(shuffled)
    
    recommendations = []
    for movie in shuffled[:count]:
        recommendations.append({
            "id": movie["id"],
            "title": movie["title"],
            "genres": movie["genres"],
            "score": movie["rating"],
            "source": source
        })
    
    return recommendations

if __name__ == '__main__':
    print("🚀 Starting SmartFlix API Server...")
    print("📡 Server will run on: http://0.0.0.0:5000")
    print("💡 Make sure your ESP32 uses your computer's IP address")
    app.run(host='0.0.0.0', port=5000, debug=True)