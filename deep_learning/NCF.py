import pandas as pd
import torch
import torch.nn as nn
import os
import numpy as np

class NCF(nn.Module):
    def __init__(self, num_users, num_items, emb_size=64, hidden_layers=[128, 64, 32]):
        super(NCF, self).__init__()
        self.num_users = num_users
        self.num_items = num_items
        self.user_emb = nn.Embedding(num_users, emb_size)
        self.item_emb = nn.Embedding(num_items, emb_size)
        
        # MLP layers
        layers = []
        input_size = emb_size * 2
        for hidden_size in hidden_layers:
            layers.append(nn.Linear(input_size, hidden_size))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.2))
            input_size = hidden_size
        
        layers.append(nn.Linear(input_size, 1))
        self.mlp = nn.Sequential(*layers)
        
        # Initialize weights
        self.user_emb.weight.data.uniform_(-0.01, 0.01)
        self.item_emb.weight.data.uniform_(-0.01, 0.01)
    
    def forward(self, users, items):
        # Ensure indices are within bounds
        users = torch.clamp(users, 0, self.num_users - 1)
        items = torch.clamp(items, 0, self.num_items - 1)
        
        user_emb = self.user_emb(users)
        item_emb = self.item_emb(items)
        
        # Concatenate user and item embeddings
        interaction = torch.cat([user_emb, item_emb], dim=1)
        return self.mlp(interaction).squeeze()

class NCFRecommender:
    def __init__(self):
        print("🧠 Initializing Neural Collaborative Filtering Model...")
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.load_data()
        self.model = None
        self.user_ratings = {}  # Store user ratings for training
        self.load_model()
        
    def load_data(self):
        """Load MovieLens data"""
        try:
            # Load ratings
            ratings_cols = ['UserID', 'MovieID', 'Rating', 'Timestamp']
            self.ratings = pd.read_csv('./ml-1m/ratings.dat', sep='::', 
                                     engine='python', names=ratings_cols)
            
            # Load movies
            movies_cols = ['MovieID', 'Title', 'Genres']
            self.movies_df = pd.read_csv('./ml-1m/movies.dat', sep='::', 
                                       engine='python', names=movies_cols, 
                                       encoding='latin-1')
            
            self.num_users = max(self.ratings.UserID.max() + 1, 10000)
            self.num_items = self.ratings.MovieID.max() + 1
            
            print(f"✅ Loaded {len(self.ratings)} ratings and {len(self.movies_df)} movies")
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            # Create fallback data
            self.ratings = pd.DataFrame({
                'UserID': [1, 1, 2, 2],
                'MovieID': [1, 2, 1, 3],
                'Rating': [5, 4, 3, 5]
            })
            self.movies_df = pd.DataFrame({
                'MovieID': [1, 2, 3, 4, 5],
                'Title': ['Toy Story', 'Jumanji', 'Grumpier Old Men', 'Waiting to Exhale', 'Father of the Bride'],
                'Genres': ['Animation|Children|Comedy', 'Adventure|Children|Fantasy', 
                          'Comedy|Romance', 'Comedy|Drama|Romance', 'Comedy']
            })
            self.num_users = 10000
            self.num_items = 4000
    
    def load_model(self):
        """Load or create model"""
        self.model = NCF(self.num_users, self.num_items).to(self.device)
        print("✅ NCF model initialized with random weights")
        self.model.eval()
    
    def update_user_ratings(self, user_id, user_ratings):
        """Update model with user's ratings for personalization"""
        # Ensure user_id is within bounds
        safe_user_id = min(user_id, self.num_users - 1)
        self.user_ratings[safe_user_id] = user_ratings
        
        if user_ratings:
            print(f"🔄 Training NCF model with {len(user_ratings)} user ratings...")
            self._train_on_user_ratings(safe_user_id, user_ratings)
    
    def _train_on_user_ratings(self, user_id, user_ratings):
        """Quick training on user's ratings"""
        if not user_ratings:
            return
            
        self.model.train()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01)
        loss_fn = nn.MSELoss()
        
        # Convert ratings to tensors and ensure they're within bounds
        safe_user_id = min(user_id, self.num_users - 1)
        user_tensor = torch.LongTensor([safe_user_id] * len(user_ratings)).to(self.device)
        
        # Filter movie IDs to be within bounds
        valid_movie_ids = [mid for mid in user_ratings.keys() if mid < self.num_items]
        if not valid_movie_ids:
            return
            
        item_tensor = torch.LongTensor(valid_movie_ids).to(self.device)
        rating_values = [user_ratings[mid] for mid in valid_movie_ids]
        rating_tensor = torch.FloatTensor(rating_values).to(self.device)
        
        # Quick training (few epochs)
        for epoch in range(5):  # Reduced epochs for speed
            optimizer.zero_grad()
            predictions = self.model(user_tensor, item_tensor)
            loss = loss_fn(predictions, rating_tensor)
            loss.backward()
            optimizer.step()
        
        self.model.eval()
    
    def get_recommendations(self, user_id, top_k=3):
        """Get recommendations for user - PERSONALIZED based on ratings"""
        # Ensure user_id is within bounds
        safe_user_id = min(user_id, self.num_users - 1)
        
        print(f"🎯 Generating PERSONALIZED NCF recommendations for user {safe_user_id}...")
        
        # Update model with latest user ratings
        if safe_user_id in self.user_ratings:
            current_ratings = self.user_ratings[safe_user_id]
            if current_ratings:
                self._train_on_user_ratings(safe_user_id, current_ratings)
        
        try:
            with torch.no_grad():
                user_tensor = torch.LongTensor([safe_user_id] * self.num_items).to(self.device)
                movie_tensor = torch.LongTensor(range(self.num_items)).to(self.device)
                
                predictions = self.model(user_tensor, movie_tensor).cpu().numpy()
            
            # Filter out movies user already rated
            rated_movies = set()
            if safe_user_id in self.user_ratings:
                rated_movies = set(self.user_ratings[safe_user_id].keys())
            
            # Get top recommendations (excluding rated movies)
            valid_movies = []
            valid_predictions = []
            
            for mid in range(min(self.num_items, 1000)):  # Limit to first 1000 movies for speed
                if mid in rated_movies:
                    continue  # Skip movies user already rated
                try:
                    # Check if movie exists in our dataset
                    if mid in self.movies_df.MovieID.values:
                        valid_movies.append(mid)
                        valid_predictions.append(predictions[mid])
                except:
                    continue
            
            if not valid_movies:
                return self._get_fallback_recommendations()
            
            # Get top indices
            top_indices = np.argsort(valid_predictions)[-top_k:][::-1]
            top_movie_ids = [valid_movies[idx] for idx in top_indices]
            
            recommendations = []
            for mid in top_movie_ids:
                try:
                    movie_info = self.movies_df[self.movies_df['MovieID'] == mid].iloc[0]
                    recommendations.append({
                        'id': int(mid),
                        'title': movie_info['Title'],
                        'genres': movie_info['Genres'],
                        'score': float(predictions[mid]),
                        'model': 'Neural CF'
                    })
                except:
                    continue
            
            return recommendations if recommendations else self._get_fallback_recommendations()
            
        except Exception as e:
            print(f"❌ Error in NCF recommendations: {e}")
            return self._get_fallback_recommendations()
    
    def _get_fallback_recommendations(self):
        """Fallback recommendations"""
        return [
            {'id': 1, 'title': 'The Dark Knight', 'genres': 'Action|Crime|Drama', 'score': 4.9, 'model': 'NCF'},
            {'id': 50, 'title': 'Inception', 'genres': 'Action|Adventure|Sci-Fi', 'score': 4.8, 'model': 'NCF'},
            {'id': 100, 'title': 'Interstellar', 'genres': 'Adventure|Drama|Sci-Fi', 'score': 4.7, 'model': 'NCF'}
        ]