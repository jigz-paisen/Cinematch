import streamlit as st
import pickle
import pandas as pd
import numpy as np
import requests
import base64

# Load your data and similarity matrix
@st.cache(allow_output_mutation=True)
def load_data():
    with open('tmdb_data_list.pkl', 'rb') as file:
        tmdb_data = pickle.load(file)
    with open('similarity.pkl', 'rb') as file:
        similarity = pickle.load(file)
    return tmdb_data, similarity

tmdb_data, similarity = load_data()


# Function to display a welcome message
def show_welcome_message():
    st.title("Welcome to Cinematch!")
    st.markdown("""
        🎬 **Your Personal Movie Recommender.**
        
        Get started by selecting options in the sidebar menu. You can search movies by **Title**, **Genre**, or **Year**.
        
        If you're on a mobile device, tap on the [>] icon at the top-left corner to open the sidebar menu and begin exploring!
    """)

# Call the welcome message function at the beginning of your app
show_welcome_message()


# Function to get image data for use in custom HTML/CSS
def get_image_data_as_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

# Path to your image
logo_path = 'image/logo.webp'
image_path = 'image/helplogo.webp'

# Convert the image to base64 for HTML embedding
image_base64 = get_image_data_as_base64(logo_path)
logo_base64 = get_image_data_as_base64(image_path)

# The WhatsApp number to be contacted
whatsapp_number = "233551045609"  

# Custom UI adjustments with CSS
st.sidebar.markdown(f"""
    <style>
    .sidebar-logo {{
        height: auto;
        width: 40%;  /* Adjust the size to fit your needs */
        border-radius: 50%;  /* Makes the image round */
        display: block;
        margin-left: auto;
        margin-right: auto;
        margin-bottom: 12%
    }}
    </style>
    <img class="sidebar-logo" src="data:image/webp;base64,{image_base64}">
    """, unsafe_allow_html=True)


# Extracting unique titles, genres, and years after loading data
titles = tmdb_data['title'].sort_values().unique().tolist()
genres = sorted(set([genre for sublist in tmdb_data['genres'].str.split(', ').tolist() for genre in sublist]))
years = sorted(tmdb_data['release_year'].unique().tolist())

# Sidebar for user inputs
# Custom Sidebar Title with HTML and CSS
st.sidebar.markdown("""
    <style>
    .sidebar-title {
        font-size:24px !important;
        font-weight: bold;
        color: #FFFFFF; /* Change the color to fit your theme */
        padding: 10px;
        text-align: left; /* Center align the title */
        background-color: #363C47; /* Light background color for the title */
        border-radius: 10px; /* Rounded corners for the background */
        margin-bottom: 20px; /* Space below the title */
    }
    /* Additional styles for the sidebar */
    .css-1d391kg {
        padding-top: 0rem;
    }
    </style>
    <div class="sidebar-title">🎬 Cinematch</div>
    """, unsafe_allow_html=True)

st.sidebar.markdown("""
    <style>
    .font {
        font-size:16px;
    }
    </style>
    <div class='font'>
        Your Personal Movie Recommender
    </div>    
    """, unsafe_allow_html=True)

search_category = st.sidebar.radio("Search by", ("Title", "Genre", "Year"), help="Select how you want to search for movies.")

if search_category == "Title":
    selected = st.sidebar.selectbox("Choose a movie title", titles, help="Select a movie title from the list.")
elif search_category == "Genre":
    selected = st.sidebar.selectbox("Choose a genre", genres, help="Select a movie genre from the list.")
else:  # "Year"
    selected = st.sidebar.selectbox("Choose a year", years, help="Select a release year from the list.")
    
# Define fetch poster functions
def fetch_poster(movie_id, progress_increment, current_progress):
    api_key = "c7ec19ffdd3279641fb606d19ceb9bb1"  # Your TMDb API key
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            full_path = f"https://image.tmdb.org/t/p/w500{poster_path}"
            return full_path
        else:
            st.error("Poster path not found in API response.")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching poster: {e}")
        return None
    finally:
        # Update progress
        if current_progress:
            current_progress.progress(progress_increment)


# Define recommendation functions
def recommend_movies_with_posters(recommended_movies):
    movies_id = recommended_movies['id'].tolist()
    if movies_id:
        progress_bar = st.progress(0)
        fetching_text = st.empty()  # Placeholder for dynamic text
        posters = []

        for i, movie_id in enumerate(movies_id):
            # Update fetching text
            fetching_text.text(f"Fetching movie recommendations: {i+1}/{len(movies_id)}")
            
            progress_increment = 100 // len(movies_id)
            poster = fetch_poster(movie_id, progress_increment, progress_bar)
            posters.append(poster)

            # Update progress bar
            progress_bar.progress(min(100, (i + 1) * progress_increment))

        progress_bar.empty()  # Remove the progress bar after completion
        fetching_text.empty()  # Clear the fetching text
    else:
        st.write("No movies to fetch posters for.")
        posters = []

    return recommended_movies, posters


def recommend_movies_by_title(title):
    idx = tmdb_data.index[tmdb_data['title'] == title].tolist()[0]
    sim_scores = list(enumerate(similarity[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    movie_indices = [i[0] for i in sim_scores[1:11]]
    recommended_movies = tmdb_data.iloc[movie_indices]

    # Fetch poster URLs using the movie IDs
    return recommend_movies_with_posters(recommended_movies)

def recommend_movies_by_genre(genre):
    filtered_movies = tmdb_data[tmdb_data['genres'].str.contains(genre, case=False, na=False)]
    recommended_movies = filtered_movies.sort_values(by='rating', ascending=False).head(10)

    # Fetch poster URLs using the movie IDs
    return recommend_movies_with_posters(recommended_movies)

def recommend_movies_by_year(year):
    filtered_movies = tmdb_data[tmdb_data['release_year'] == year]
    recommended_movies = filtered_movies.sort_values(by='rating', ascending=False).head(10)

    # Fetch poster URLs using the movie IDs
    return recommend_movies_with_posters(recommended_movies)


# Assuming you have a column 'id' in your tmdb_data DataFrame that corresponds to the TMDb movie ID
TMDB_BASE_URL = "https://www.themoviedb.org/movie/"


# Display recommendations based on user selection
if st.sidebar.button('Get Recommendations'):
    if search_category == "Title":
        recommendations, posters = recommend_movies_by_title(selected)  # Ensure this returns both movies and their posters
    elif search_category == "Genre":
        # For genres and years, you might need to modify the functions or logic to fetch posters as well
        recommendations , posters= recommend_movies_by_genre(selected)
    else:  # "Year"
        recommendations, posters = recommend_movies_by_year(int(selected))

    if not recommendations.empty:
        st.write("### Recommendations:")
        # Use enumerate to keep track of the index properly
        for i, (idx, movie) in enumerate(recommendations.iterrows()):
            poster = posters[i] if i < len(posters) else None  # Safeguard against index error
            
            # Constructing the URL to the TMDb page for the movie
            movie_url = f"{TMDB_BASE_URL}{movie['id']}"

            col1, col2 = st.columns([1, 4])
            with col1:
                # Display poster if available
                if poster:
                    st.image(poster, width=100)
                else:
                    st.write("No poster available")
            with col2:
                # Make the movie title a clickable link to the TMDb page
                st.markdown(f"**[Title: {movie['title']}]({movie_url})**", unsafe_allow_html=True)
                st.write(f"**Genres:** {movie['genres']}")
                st.write(f"**Release Year:** {movie['release_year']}")
                st.write(f"**Rating:** {movie['rating']}")
                st.write("---")
    
    else:
        st.write("No recommendations found.")
        

# Add contact information to the sidebar
st.sidebar.markdown("### Need Help?")
# HTML to embed the clickable image
image_html = f"""
    <div style="display: flex; align-items: center; justify-content: space-around;">
        <a href="https://wa.me/{whatsapp_number}" target="_blank">
            <img src="data:image/webp;base64,{logo_base64}" alt="WhatsApp helpline" style="border-radius: 50%; width: 50px; height: 50px;"/>
        </a>
        <p style="margin: 0;">Chat with @prodigygenes</p>
    </div>
"""

# Place the clickable image and text in the sidebar
st.sidebar.markdown(image_html, unsafe_allow_html=True)


# At the bottom of your Streamlit app's sidebar code
st.sidebar.markdown("""
    <div style='margin-top: 40%;'>
        <hr/>
    </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown("""
    <p style="font-size: 14px; text-align: center;">
        &copy; 2024 CineMatch. All Rights Reserved.
    </p>
    """, unsafe_allow_html=True)


