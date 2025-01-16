import pickle
import streamlit as st
import requests
import json
import os

# Function to fetch poster, release year, rating, and language using TMDb API
def fetch_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=052c588315f0bb2158fdf3a816b2cf13&language=en-US"
    try:
        data = requests.get(url).json()
        poster_path = data.get('poster_path', '')
        release_date = data.get('release_date', '')
        release_year = release_date.split('-')[0] if release_date else "N/A"
        rating = data.get('vote_average', 'N/A')  # Fetch rating
        language = data.get('original_language', 'N/A').upper()  # Fetch language and convert to uppercase

        if poster_path:
            full_path = f"http://image.tmdb.org/t/p/w500/{poster_path}"
        else:
            # Default poster if none is found
            full_path = "https://via.placeholder.com/500x750.png?text=No+Image+Available"
        
        return full_path, release_year, rating, language
    except Exception as e:
        st.error(f"Error fetching movie details: {e}")
        return "https://via.placeholder.com/500x750.png?text=No+Image+Available", "N/A", "N/A", "N/A"

# Function to fetch movies by release date
def fetch_movies_by_date(start_year, end_year):
    url = f"https://api.themoviedb.org/3/discover/movie?api_key=052c588315f0bb2158fdf3a816b2cf13&language=en-US&sort_by=release_date.asc&primary_release_date.gte={start_year}-01-01&primary_release_date.lte={end_year}-12-31"
    data = requests.get(url).json()
    movie_details = []
    for movie in data['results'][:20]:  # Fetch top 20 movies within the date range
        poster, release_year, rating, language = fetch_movie_details(movie['id'])
        movie_details.append({
            "title": f"{movie['title']} ({release_year})",
            "poster": poster,
            "rating": rating,
            "language": language,
            "release_date": movie.get('release_date', '')  # Add release_date for sorting
        })

    # Sort the movies by release_date in ascending order
    movie_details.sort(key=lambda x: x['release_date'] if x['release_date'] else "")
    return movie_details

# Function to fetch trending movies
def fetch_trending_movies():
    url = "https://api.themoviedb.org/3/trending/movie/day?api_key=052c588315f0bb2158fdf3a816b2cf13"
    data = requests.get(url).json()
    movie_details = []
    for movie in data['results'][:20]:  # Fetch top 20 trending movies
        poster, release_year, rating, language = fetch_movie_details(movie['id'])
        movie_details.append({
            "title": f"{movie['title']} ({release_year})",
            "poster": poster,
            "rating": rating,
            "language": language
        })
    return movie_details

# Function to fetch recently released movies
def fetch_recent_movies():
    url = "https://api.themoviedb.org/3/movie/now_playing?api_key=052c588315f0bb2158fdf3a816b2cf13&language=en-US&page=1"
    data = requests.get(url).json()
    movie_details = []
    for movie in data['results'][:20]:  # Fetch top 20 recently released movies
        poster, release_year, rating, language = fetch_movie_details(movie['id'])
        movie_details.append({
            "title": f"{movie['title']} ({release_year})",
            "poster": poster,
            "rating": rating,
            "language": language
        })
    return movie_details

# Function to recommend movies
def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movies = []
    for i in distances[1:11]:  # Top 10 recommendations
        movie_id = movies.iloc[i[0]].movie_id
        poster, release_year, rating, language = fetch_movie_details(movie_id)
        recommended_movies.append({
            "title": f"{movies.iloc[i[0]].title} ({release_year})",
            "poster": poster,
            "rating": rating,
            "language": language
        })
    return recommended_movies

# Function to display movies
def display_movies(movie_details):
    for i in range(0, len(movie_details), 5):  # Loop through 5 movies per row
        cols = st.columns(5)  # Create 5 columns
        for j, col in enumerate(cols):
            if i + j < len(movie_details):  # Check to avoid index out of range
                with col:
                    movie = movie_details[i + j]
                    # Split title and release year for display
                    title, release_year = movie['title'].rsplit('(', 1)
                    release_year = release_year.strip(')')  # Remove trailing parenthesis
                    st.markdown(
                        f"""
                        <style>
                        .movie-card {{
                            text-align: center;
                            border-radius: 10px;
                            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
                            overflow: hidden;
                            margin-bottom: 15px;
                            height: 370px; /* Fixed height for the entire container */
                            display: flex;
                            flex-direction: column;
                            justify-content: space-between;
                        }}
                        .movie-poster {{
                            position: relative;
                            border-radius: 10px;
                            overflow: hidden;
                            height: 300px; /* Fixed height for poster */
                        }}
                        .movie-poster img {{
                            width: 100%;
                            height: 100%;
                            border-radius: 10px;
                            object-fit: cover;
                        }}
                        .movie-poster .rating-overlay {{
                            position: absolute;
                            top: 0;
                            left: 0;
                            width: 100%;
                            height: 100%;
                            background: rgba(0, 0, 0, 0.6);
                            color: #fff;
                            font-size: 16px;
                            font-weight: bold;
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            justify-content: center;
                            opacity: 0;
                            transition: opacity 0.3s ease;
                        }}
                        .movie-poster:hover .rating-overlay {{
                            opacity: 1;
                        }}
                        .movie-details {{
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            justify-content: center;
                            height: 70px;
                        }}
                        .movie-title {{
                            font-weight: bold;
                            font-size: 14px;
                            color: #333;
                            line-height: 1.2;
                        }}
                        .release-year {{
                            font-size: 12px;
                            color: #888;
                        }}
                        </style>

                        <div class="movie-card">
                            <div class="movie-poster">
                                <img src="{movie['poster']}" alt="{title}">
                                <div class="rating-overlay">
                                    <div>Rating: {movie['rating']}</div>
                                    <div>Language: {movie['language']}</div>
                                </div>
                            </div>
                            <div class="movie-details">
                                <div class="movie-title">{title.strip()}</div>
                                <div class="release-year">({release_year})</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

# File to store user data
USER_DATA_FILE = "user_data.json"

# Function to load user data
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as file:
            return json.load(file)
    return {}

# Function to save user data
def save_user_data(data):
    with open(USER_DATA_FILE, "w") as file:
        json.dump(data, file)

# Streamlit app
st.set_page_config(layout="wide")  # Set layout to wide for better UI

st.markdown(
    """
    <div style="display: flex; align-items: center; justify-content: center; margin-top: 20px;">
        <span style="font-size: 40px; margin-right: 15px;">🎬</span>
        <h1 style="margin: 0; font-size: 50px;">Movie Recommender System</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# Load the movie data and similarity model
movies = pickle.load(open('E:/Recommendation System/artifacts/movie_list.pkl', 'rb'))
similarity = pickle.load(open('E:/Recommendation System/artifacts/similarity.pkl', 'rb'))

# Load user data
user_data = load_user_data()

st.sidebar.markdown(
    """
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <span style="font-size: 20px; margin-right: 10px;">🎬</span>
        <h2 style="margin: 0;">Explore Movies</h2>
    </div>
    """,
    unsafe_allow_html=True,
)

selected_section = st.sidebar.radio(
    "Choose a section:",
    ("Recommendations", "Trending Movies", "Recently Released", "Movies by Release Date")
)

# Add release date slider
start_year, end_year = st.sidebar.slider(
    "Select a release year range:",
    min_value=1916,
    max_value=2017,
    value=(2000, 2010),  # Default range
    step=1
)

# Recommendations section
if selected_section == "Recommendations":
    st.sidebar.subheader("Select a movie for recommendations")
    movie_list = movies['title'].values
    selected_movie = st.sidebar.selectbox(
        "Type or select a movie from the dropdown",
        [""] + list(movie_list),  # Add an empty default option
        index=0  # Default to the empty option
    )

    if selected_movie:  # Check if a movie is selected
        # Save the selected movie in user data
        user_data['last_movie'] = selected_movie
        save_user_data(user_data)

        st.subheader(f"Recommendations for {selected_movie}:")
        recommended_movies = recommend(selected_movie)
        display_movies(recommended_movies)
    elif 'last_movie' in user_data:
        # Display recommendations for the last movie
        last_movie = user_data['last_movie']
        st.subheader(f"Recommendations from your last searched movie")
        recommended_movies = recommend(last_movie)
        display_movies(recommended_movies)
    else:
        st.subheader("Select a movie from the dropdown for recommendations")

# Display content based on the selected section
if selected_section == "Trending Movies":
    st.subheader("Trending Movies")
    trending_movies = fetch_trending_movies()
    display_movies(trending_movies)

elif selected_section == "Recently Released":
    st.subheader("Recently Released Movies")
    recent_movies = fetch_recent_movies()
    display_movies(recent_movies)

elif selected_section == "Movies by Release Date":
    st.subheader(f"Movies Released Between {start_year} and {end_year}")
    filtered_movies = fetch_movies_by_date(start_year, end_year)
    display_movies(filtered_movies)