import torch
import json
import os
import sys
from iot.simulator import IoTDevice
from utils import display_movies, get_user_ratings, clear_screen

class SmartFlix:
    def __init__(self):
        clear_screen()
        print("🎬 SMARTFLIX - Movie Recommendation System")
        print("=" * 50)
        
        # Initialize IoT Device
        self.iot_device = IoTDevice()
        self.iot_device.start()
        
        # Load AI Models
        self.load_ai_models()
        self.load_users()
        
        print("✅ System ready!")
    
    def load_ai_models(self):
        """Load deep learning models"""
        print("\n🧠 Loading AI models...")
        try:
            sys.path.append('./deep_learning')
            from MF import MFRecommender
            from NCF import NCFRecommender
            
            self.mf_model = MFRecommender()
            self.ncf_model = NCFRecommender()
            self.ai_loaded = True
            print("✅ AI models loaded!")
            
        except Exception as e:
            print(f"❌ AI models not available: {e}")
            self.ai_loaded = False
    
    def load_users(self):
        """Load user data"""
        if os.path.exists('users.json'):
            with open('users.json', 'r') as f:
                self.users_data = json.load(f)
        
        # Convert any string ratings to integers
        for username, user_data in self.users_data.get("users", {}).items():
            if "rated_movies" in user_data:
                # Convert string values to integers
                user_data["rated_movies"] = {int(k): int(v) for k, v in user_data["rated_movies"].items()}
        
        if not os.path.exists('users.json'):
            self.users_data = {"user_id_counter": 10000, "users": {}}
    
    def save_users(self):
        """Save user data"""
        with open('users.json', 'w') as f:
            json.dump(self.users_data, f, indent=2)
    
    def get_or_create_user(self, username):
        """Get existing user or create new one"""
        if username in self.users_data["users"]:
            user_data = self.users_data["users"][username]
            # Ensure ratings are integers
            rated_movies = user_data.get("rated_movies", {})
            rated_movies = {int(k): int(v) for k, v in rated_movies.items()}
            return user_data["id"], rated_movies
        else:
            user_id = self.users_data["user_id_counter"]
            self.users_data["user_id_counter"] += 1
            self.users_data["users"][username] = {
                "id": user_id, 
                "rated_movies": {}
            }
            self.save_users()
            return user_id, {}
    
    def main_menu(self):
        """Main terminal interface"""
        clear_screen()
        print("\n👤 USER LOGIN")
        print("-" * 30)
        username = input("Enter your username: ").strip()
        if not username:
            username = "guest"
        
        user_id, user_ratings = self.get_or_create_user(username)
        
        # For new users, ask for ratings first
        if not user_ratings:
            print(f"\n👋 Welcome {username}! Let's get to know your taste.")
            user_ratings = self.rate_movies(username, user_id, user_ratings)
        
        while True:
            clear_screen()
            print(f"\n🤖 SMARTFLIX - Welcome {username}!")
            print("=" * 40)
            print("1. 🎯 Get Movie Recommendations")
            print("2. ⭐ Rate More Movies")
            print("3. 🎮 IoT Interactions")
            print("4. 📊 AI Model Comparison")
            print("0. 🚪 Exit")
            print("=" * 40)
            
            choice = input("\nEnter choice (0-4): ").strip()
            
            if choice == '1':
                self.get_recommendations(user_id, user_ratings)
            elif choice == '2':
                user_ratings = self.rate_movies(username, user_id, user_ratings)
            elif choice == '3':
                self.iot_interactions(user_id, user_ratings)
            elif choice == '4':
                self.compare_models(user_id, user_ratings)
            elif choice == '0':
                self.shutdown()
                break
            else:
                print("❌ Invalid choice")
                input("Press Enter to continue...")
    
    def get_recommendations(self, user_id, user_ratings):
        """Get personalized recommendations - SHOW TOP 3 MOVIES"""
        clear_screen()
        print("\n🎯 GETTING RECOMMENDATIONS")
        print("=" * 40)
        
        # Ensure ratings are integers
        user_ratings = {int(k): int(v) for k, v in user_ratings.items()}
        
        # UPDATE MODELS WITH USER RATINGS BEFORE GETTING RECOMMENDATIONS
        if self.ai_loaded and user_ratings:
            print("🔄 Updating AI models with your ratings...")
            try:
                self.mf_model.update_user_ratings(user_id, user_ratings)
                self.ncf_model.update_user_ratings(user_id, user_ratings)
                print("✅ Models updated successfully!")
            except Exception as e:
                print(f"⚠️  Error updating models: {e}")
                print("Using fallback recommendations...")
        
        # Choose model based on user ratings
        if len(user_ratings) >= 3:
            print("🧠 Using Neural CF (you have enough ratings)")
            model_type = "NCF"
        else:
            print("⚡ Using Matrix Factorization (good start!)")
            model_type = "MF"
        
        self.iot_device.record_interaction("button_press")
        
        if not self.ai_loaded:
            recommendations = self._get_fallback_recommendations()
        else:
            try:
                if model_type == "MF":
                    recommendations = self.mf_model.get_recommendations(user_id, 3)
                else:
                    recommendations = self.ncf_model.get_recommendations(user_id, 3)
            except Exception as e:
                print(f"❌ Error getting {model_type} recommendations: {e}")
                recommendations = self._get_fallback_recommendations()
        
        print(f"\n🎬 TOP 3 RECOMMENDATIONS FOR YOU ({model_type}):")
        print("=" * 50)
        display_movies(recommendations)
        
        print(f"⭐ Based on your {len(user_ratings)} ratings")
        
        if user_ratings:
            print(f"📊 Your ratings: {user_ratings}")
        
        self.iot_device.led_feedback("success")
        
        input("\nPress Enter to continue...")
    
    def rate_movies(self, username, user_id, user_ratings):
        """Rate movies to improve recommendations"""
        clear_screen()
        print("\n⭐ RATE MOVIES")
        print("=" * 40)
        
        if not user_ratings:
            print("Let's rate some movies to personalize your experience!")
        else:
            print(f"You've rated {len(user_ratings)} movies. Rate more to improve!")
        
        # Use actual movie IDs from the dataset (popular movies from MovieLens)
        movies_to_rate = [
            {'id': 1, 'title': 'Toy Story', 'genres': 'Animation|Children|Comedy'},
            {'id': 50, 'title': 'The Usual Suspects', 'genres': 'Crime|Mystery|Thriller'},
            {'id': 100, 'title': 'Fargo', 'genres': 'Comedy|Crime|Drama|Thriller'},
            {'id': 150, 'title': 'Apollo 13', 'genres': 'Adventure|Drama|IMAX'},
            {'id': 200, 'title': 'The Silence of the Lambs', 'genres': 'Crime|Horror|Thriller'},
            {'id': 250, 'title': 'The Shawshank Redemption', 'genres': 'Drama'},
            {'id': 300, 'title': 'Forrest Gump', 'genres': 'Comedy|Drama|Romance'},
            {'id': 350, 'title': 'Pulp Fiction', 'genres': 'Comedy|Crime|Drama'}
        ]
        
        print("\n🎬 Movies to Rate:")
        for i, movie in enumerate(movies_to_rate, 1):
            print(f"{i}. {movie['title']}")
            print(f"   Genres: {movie['genres']}")
        
        print("\nRate movies (1-8) or 'done' to finish:")
        new_ratings = get_user_ratings()
        
        # Convert to actual movie IDs and ensure integers
        for movie_num, rating in new_ratings.items():
            if 1 <= movie_num <= len(movies_to_rate):
                movie_id = movies_to_rate[movie_num - 1]['id']
                user_ratings[int(movie_id)] = int(rating)  # Ensure both are integers
                print(f"✅ Rated '{movies_to_rate[movie_num - 1]['title']}' with {rating} stars")
        
        # Update user data
        if new_ratings:
            self.users_data["users"][username]["rated_movies"] = user_ratings
            self.save_users()
            print(f"✅ Saved {len(new_ratings)} ratings!")
            
            # Update AI models with new ratings immediately
            if self.ai_loaded and user_ratings:
                print("🔄 Training AI models with your new ratings...")
                try:
                    self.mf_model.update_user_ratings(user_id, user_ratings)
                    self.ncf_model.update_user_ratings(user_id, user_ratings)
                    print("✅ AI models updated successfully!")
                except Exception as e:
                    print(f"⚠️  Error updating AI models: {e}")
                    print("But your ratings were saved!")
            
            self.iot_device.record_interaction("voice_command")
        
        input("\nPress Enter to continue...")
        return user_ratings
    
    def iot_interactions(self, user_id, user_ratings):
        """IoT interaction menu"""
        clear_screen()
        print("\n🎮 IOT INTERACTIONS")
        print("=" * 40)
        print("1. 🎤 Voice Command")
        print("2. 📱 Tilt Gesture")
        print("3. 🔘 Button Press")
        print("4. 🔄 All Combined")
        print("0. ↩️  Back")
        
        choice = input("\nEnter choice (0-4): ").strip()
        
        if choice == '1':
            self.voice_interaction(user_id, user_ratings)
        elif choice == '2':
            self.tilt_interaction(user_id, user_ratings)
        elif choice == '3':
            self.button_interaction(user_id, user_ratings)
        elif choice == '4':
            self.multi_sensory_interaction(user_id, user_ratings)
        elif choice == '0':
            return
        else:
            print("❌ Invalid choice")
    
    def voice_interaction(self, user_id, user_ratings):
        """Voice command interaction"""
        clear_screen()
        print("\n🎤 VOICE COMMAND")
        print("=" * 30)
        print("Say: 'recommend action movies'")
        
        self.iot_device.record_interaction("voice_command")
        print("🎤 Processing voice command...")
        
        # Show recommendations - TOP 3 ONLY
        if not self.ai_loaded:
            recommendations = self._get_fallback_recommendations()[:3]
        else:
            try:
                recommendations = self.mf_model.get_recommendations(user_id, 3)
            except:
                recommendations = self._get_fallback_recommendations()[:3]
        
        print("\n🎬 Voice Recommendations:")
        display_movies(recommendations)
        
        input("\nPress Enter to continue...")
    
    def tilt_interaction(self, user_id, user_ratings):
        """Tilt gesture interaction"""
        clear_screen()
        print("\n📱 TILT GESTURE")
        print("=" * 30)
        print("Tilt device to navigate movies")
        
        self.iot_device.record_interaction("tilt_gesture")
        print("📱 Navigating with tilt...")
        
        if not self.ai_loaded:
            recommendations = self._get_fallback_recommendations()[:3]
        else:
            try:
                recommendations = self.ncf_model.get_recommendations(user_id, 3)
            except:
                recommendations = self._get_fallback_recommendations()[:3]
        
        print("\n🎬 Navigable Movies:")
        for i, movie in enumerate(recommendations, 1):
            print(f"{i}. {movie['title']}")
        
        input("\nPress Enter to continue...")
    
    def button_interaction(self, user_id, user_ratings):
        """Button press interaction"""
        clear_screen()
        print("\n🔘 BUTTON PRESS")
        print("=" * 30)
        print("Button pressed - refreshing recommendations")
        
        self.iot_device.record_interaction("button_press")
        
        if not self.ai_loaded:
            recommendations = self._get_fallback_recommendations()[:3]
        else:
            try:
                recommendations = self.mf_model.get_recommendations(user_id, 3)
            except:
                recommendations = self._get_fallback_recommendations()[:3]
        
        print("\n🎬 Fresh Recommendations:")
        display_movies(recommendations)
        
        input("\nPress Enter to continue...")
    
    def multi_sensory_interaction(self, user_id, user_ratings):
        """Multi-sensory interaction"""
        clear_screen()
        print("\n🔄 MULTI-SENSORY")
        print("=" * 30)
        print("Combining all sensors...")
        
        print("🎤 Voice: 'show best movies'")
        self.iot_device.record_interaction("voice_command")
        
        print("📱 Tilt: browsing")
        self.iot_device.record_interaction("tilt_gesture")
        
        print("🔘 Button: select")
        self.iot_device.record_interaction("button_press")
        
        print("🔄 Processing...")
        self.iot_device.record_interaction("multi_sensory")
        
        # Enhanced recommendations - TOP 3 ONLY
        if not self.ai_loaded:
            recommendations = self._get_fallback_recommendations()[:3]
        else:
            try:
                recommendations = self.mf_model.get_recommendations(user_id, 3)
            except:
                recommendations = self._get_fallback_recommendations()[:3]
        
        print("\n🎬 Enhanced Recommendations:")
        display_movies(recommendations)
        
        input("\nPress Enter to continue...")
    
    def compare_models(self, user_id, user_ratings):
        """Compare AI models - SHOW TOP 3 FROM EACH"""
        clear_screen()
        print("\n📊 AI MODEL COMPARISON")
        print("=" * 40)
        
        if not self.ai_loaded:
            print("❌ AI models not available")
            input("\nPress Enter to continue...")
            return
        
        try:
            mf_recs = self.mf_model.get_recommendations(user_id, 3)  # TOP 3 ONLY
            ncf_recs = self.ncf_model.get_recommendations(user_id, 3)  # TOP 3 ONLY
            
            print("⚡ Matrix Factorization (Top 3):")
            display_movies(mf_recs)
            
            print("🧠 Neural CF (Top 3):")
            display_movies(ncf_recs)
            
            # Show which model might be better
            if len(user_ratings) >= 3:
                print("💡 Neural CF works better with more ratings!")
            else:
                print("💡 Matrix Factorization is great for new users!")
            
            self.iot_device.record_comparison()
        except Exception as e:
            print(f"❌ Error comparing models: {e}")
            print("Using fallback recommendations...")
            fallback = self._get_fallback_recommendations()[:3]
            print("⚡ Fallback Recommendations:")
            display_movies(fallback)
        
        input("\nPress Enter to continue...")
    
    def shutdown(self):
        """Shutdown system"""
        print("\n🔄 Shutting down...")
        self.iot_device.stop()
        print("🎬 Thank you for using SmartFlix!")
    
    def _get_fallback_recommendations(self):
        """Fallback recommendations"""
        return [
            {'id': 1, 'title': 'Toy Story', 'genres': 'Animation|Children|Comedy', 'score': 4.8, 'model': 'Popular'},
            {'id': 50, 'title': 'The Usual Suspects', 'genres': 'Crime|Mystery|Thriller', 'score': 4.7, 'model': 'Popular'},
            {'id': 100, 'title': 'Fargo', 'genres': 'Comedy|Crime|Drama', 'score': 4.9, 'model': 'Popular'}
        ]

if __name__ == "__main__":
    try:
        smartflix = SmartFlix()
        smartflix.main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")