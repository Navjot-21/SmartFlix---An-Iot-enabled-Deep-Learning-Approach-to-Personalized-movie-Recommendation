import os
import platform

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def display_movies(movies):
    """Display movies in a formatted way"""
    for i, movie in enumerate(movies, 1):
        print(f"{i}. {movie['title']}")
        print(f"   🎭 Genres: {movie['genres']}")
        print(f"   ⭐ Score: {movie['score']:.1f}")
        print(f"   🤖 Model: {movie.get('model', 'Unknown')}")
        print()

def get_user_ratings():
    """Get movie ratings from user"""
    ratings = {}
    
    while True:
        choice = input("Enter movie number (1-8) or 'done': ").strip().lower()
        if choice == 'done':
            break
        
        try:
            movie_num = int(choice)
            if 1 <= movie_num <= 8:
                rating = input(f"Rate movie {movie_num} (1-5): ").strip()
                if rating in ['1','2','3','4','5']:
                    ratings[movie_num] = int(rating)
                    print(f"✅ Rated {rating} stars")
                else:
                    print("❌ Please enter 1-5")
            else:
                print("❌ Please enter 1-8")
        except:
            print("❌ Please enter a number")
    
    return ratings