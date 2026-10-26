import streamlit as st
import pandas as pd
import json
import os

# 1- DATA MANAGEMENT (with mock db)
MOVIES_FILE = 'movies.csv'
USERS_FILE = 'users.json'

def init_db():
    """Initialize CSV and JSON databases if they don't exist."""
    if not os.path.exists(MOVIES_FILE):
        data = {
            'ID': [1, 2, 3, 4, 5],
            'Title': ['Inception', 'The Matrix', 'Toy Story', 'The Dark Knight', 'Finding Nemo'],
            'Genre': ['Sci-Fi', 'Sci-Fi', 'Animation', 'Action', 'Animation'],
            'Views': [150, 200, 300, 250, 180],
            'Avg_Rating': [4.8, 4.7, 4.5, 4.9, 4.4]
        }
        pd.DataFrame(data).to_csv(MOVIES_FILE, index=False)
        
    if not os.path.exists(USERS_FILE):
        users_data = {
            "alice": {"history": ["Inception", "The Matrix"], "ratings": {"Inception": 5, "The Matrix": 4}, "preferences": ["Sci-Fi", "Action"]},
            "bob": {"history": ["Toy Story"], "ratings": {"Toy Story": 5}, "preferences": ["Animation"]}
        }
        with open(USERS_FILE, 'w') as f:
            json.dump(users_data, f)

def load_movies():
    return pd.read_csv(MOVIES_FILE)

def save_movies(df):
    df.to_csv(MOVIES_FILE, index=False)

def load_users():
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# 2- CORE SYSTEM LOGIC (the classes)
class RecommendationEngine:
    def __init__(self, movies_df):
        self.movies_df = movies_df

    def get_trending_movies(self):
        # Sort by views and rating
        return self.movies_df.sort_values(by=['Views', 'Avg_Rating'], ascending=False).head(5)

    def get_recommendations(self, user_preferences):
        # Filter movies that match user genres, sorted by rating
        if not user_preferences:
            return self.get_trending_movies()
        
        mask = self.movies_df['Genre'].isin(user_preferences)
        recommended = self.movies_df[mask].sort_values(by='Avg_Rating', ascending=False)
        return recommended.head(5)

# 3- STREAMLIT UI and THE DASHBOARDS
st.set_page_config(page_title="AI Movie Recommender", layout="wide")
init_db()

# Session State for Login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['role'] = ""

def login_page():
    st.title("🎬 Movie Recommendation System (MRS)")
    st.write("Welcome! Please log in to continue.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("User Login")
        user_name = st.text_input("Username (try: alice or bob)").lower()
        if st.button("Login as User"):
            if user_name:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user_name
                st.session_state['role'] = "user"
                # Create new user profile if doesn't exist
                users = load_users()
                if user_name not in users:
                    users[user_name] = {"history": [], "ratings": {}, "preferences": []}
                    save_users(users)
                st.rerun()

    with col2:
        st.subheader("Admin Console")
        admin_key = st.text_input("Admin Key (try: admin123)", type="password")
        if st.button("Login as Admin"):
            if admin_key == "admin123":
                st.session_state['logged_in'] = True
                st.session_state['username'] = "Administrator"
                st.session_state['role'] = "admin"
                st.rerun()
            else:
                st.error("Invalid Admin Key")

def user_dashboard():
    st.title(f"👋 Welcome, {st.session_state['username'].capitalize()}!")
    if st.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    movies_df = load_movies()
    users = load_users()
    current_user = users[st.session_state['username']]
    engine = RecommendationEngine(movies_df)

    tab1, tab2, tab3 = st.tabs(["Home & Recommendations", "Search & Rate", "My Profile & Insights"])

    with tab1:
        st.header("Top Recommended For You")
        recs = engine.get_recommendations(current_user['preferences'])
        st.dataframe(recs[['Title', 'Genre', 'Avg_Rating']], use_container_width=True)

        st.header("🔥 Trending Movies")
        trending = engine.get_trending_movies()
        st.dataframe(trending[['Title', 'Genre', 'Views']], use_container_width=True)

    with tab2:
        st.header("Search & Rate Movies")
        search_query = st.text_input("Search for a movie title...")
        if search_query:
            results = movies_df[movies_df['Title'].str.contains(search_query, case=False)]
            st.dataframe(results[['Title', 'Genre', 'Avg_Rating']])
        
        st.subheader("Rate a Movie")
        movie_to_rate = st.selectbox("Select a movie to rate", movies_df['Title'].tolist())
        rating = st.slider("Rating (1-5)", 1, 5, 3)
        if st.button("Submit Rating"):
            # Update user profile
            current_user['ratings'][movie_to_rate] = rating
            if movie_to_rate not in current_user['history']:
                current_user['history'].append(movie_to_rate)
            
            # Auto-update genre preferences based on rated movie
            genre = movies_df.loc[movies_df['Title'] == movie_to_rate, 'Genre'].values[0]
            if genre not in current_user['preferences']:
                current_user['preferences'].append(genre)
                
            save_users(users)
            
            # Update global movie views and average rating
            idx = movies_df.index[movies_df['Title'] == movie_to_rate][0]
            movies_df.at[idx, 'Views'] += 1
            # Simple mock update for avg rating
            old_avg = movies_df.at[idx, 'Avg_Rating']
            movies_df.at[idx, 'Avg_Rating'] = round((old_avg + rating) / 2, 1)
            save_movies(movies_df)
            
            st.success(f"Rated '{movie_to_rate}' {rating} stars!")

    with tab3:
        st.header("My Watch History & Logs")
        st.write("History:", current_user['history'])
        st.write("My Ratings:", current_user['ratings'])
        st.write("My Preferred Genres:", current_user['preferences'])
        
        st.header("Top Rated Movies on Platform")
        # Visualisation requirement
        chart_data = movies_df.set_index('Title')['Avg_Rating']
        st.bar_chart(chart_data)

def admin_dashboard():
    st.title("🛡️ System Administrator Console")
    if st.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    movies_df = load_movies()

    tab1, tab2 = st.tabs(["Manage Database", "Analytics & Engagement"])

    with tab1:
        st.header("Database Management (CRUD)")
        st.dataframe(movies_df, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("Add Movie")
            with st.form("add_movie_form"):
                new_id = movies_df['ID'].max() + 1 if not movies_df.empty else 1
                new_title = st.text_input("Movie Title")
                new_genre = st.text_input("Genre")
                submitted = st.form_submit_button("Add")
                if submitted and new_title and new_genre:
                    new_row = pd.DataFrame([{'ID': new_id, 'Title': new_title, 'Genre': new_genre, 'Views': 0, 'Avg_Rating': 0.0}])
                    movies_df = pd.concat([movies_df, new_row], ignore_index=True)
                    save_movies(movies_df)
                    st.success("Added!")
                    st.rerun()

        with col2:
            st.subheader("Edit Movie")
            with st.form("edit_movie_form"):
                movie_to_edit = st.selectbox("Select Movie", movies_df['Title'].tolist())
                updated_genre = st.text_input("Update Genre (Optional)")
                edit_submitted = st.form_submit_button("Edit")
                if edit_submitted and updated_genre:
                    idx = movies_df.index[movies_df['Title'] == movie_to_edit][0]
                    movies_df.at[idx, 'Genre'] = updated_genre
                    save_movies(movies_df)
                    st.success("Updated!")
                    st.rerun()

        with col3:
            st.subheader("Remove Movie")
            with st.form("delete_movie_form"):
                movie_to_delete = st.selectbox("Select Movie to Delete", movies_df['Title'].tolist())
                delete_submitted = st.form_submit_button("Delete")
                if delete_submitted:
                    movies_df = movies_df[movies_df['Title'] != movie_to_delete]
                    save_movies(movies_df)
                    st.warning("Deleted!")
                    st.rerun()

    with tab2:
        st.header("User Engagement Trends")
        st.write("Most Watched Movies (Platform Wide)")
        # Engagement visualization
        st.bar_chart(movies_df.set_index('Title')['Views'])

        st.write("Genre Popularity")
        genre_counts = movies_df['Genre'].value_counts()
        st.line_chart(genre_counts)

# 4- APP ROUTING
if not st.session_state['logged_in']:
    login_page()
else:
    if st.session_state['role'] == 'admin':
        admin_dashboard()
    else:
        user_dashboard()