# 🎧 Recommendation Engine Exploration using Spotify Tracks


Welcome to the **Recommendation Engine** project, an intelligent system designed to suggest tracks to users based on a combination of track features, user preferences, and explainable insights. This project was built with the goal of exploring various machine learning techniques behind recommendation systems and tackling engineering challenges like data processing, scalability, and API limitations.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/render-examples/fastapi)

## 🌟 Features

- **Cosine Similarity Recommendations**: Recommends songs based on cosine similarity using audio features like danceability, energy, valence, and more.
- **Explainable Recommendations**: Provides users with insights into why certain tracks are recommended by showing feature differences and similarity scores.
- **Weighted Recommendations**: Allows users to customize the importance of different track attributes to get more personalized recommendations.
- **Data Caching and Scalability**: Uses Redis for caching responses and employs background workers for periodic updates, effectively managing API rate-limits.
- **Multiple Recommendation Algorithms**: Explores traditional methods like **k-Nearest Neighbors (k-NN)**, **Non-Negative Matrix Factorization (NMF)**, and deep learning methods like **Autoencoders**. Investigated large-scale nearest neighbors using **FAISS** and **ANNOY**.
- **Data Preprocessing & Integration**: Processed large datasets with **Pandas**, integrated **BeautifulSoup** for scraping, and used **Requests** for API interactions.

## 📚 Overview & Purpose

This project was driven by a curiosity to understand the mechanics behind recommendation engines, including both traditional machine learning and deep learning approaches. It serves as an exploration of balancing **recommendation accuracy** and **explainability** with **engineering considerations** like processing time, file sizes, and data shapes. The goal is to provide meaningful recommendations with insights that users can trust.

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+**
- **Spotify Developer Account**: Create an app on the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/) to get your `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`.
- **MongoDB Atlas**: Set up a free MongoDB Atlas cluster and get your connection string.
- **Render Account**: For deploying the service in a production-like environment.

### Local Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/recommendation-engine.git
   cd recommendation-engine
   ```

2. Set up a virtual environment and activate it:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with your credentials:

   ```
   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   MONGO_URL=your_mongodb_connection_string
   SECRET_TOKEN=your_secret_token
   ```

5. Run the FastAPI server:

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

6. Access the API documentation at:
   ```
   http://localhost:8000/docs
   ```

### Running Unit Tests

- **Note**: `conftest.py` is used to manage the directory structure with `main.py` outside the `app` directory.
- Run tests:
  ```bash
  pytest
  ```
- Run tests with coverage:
  ```bash
  pytest --cov=app
  ```
- View missing lines in coverage:
  ```bash
  pytest --cov=app --cov-report=term-missing
  ```

## 🧠 How It Works

### 1. Recommendation Logic

- Uses **cosine similarity** to measure the closeness of a target song's features with those in the database, recommending the top tracks.
- Allows for **weighted adjustments**, letting users prioritize attributes like energy or danceability in recommendations.
- Explores advanced algorithms like **Non-Negative Matrix Factorization (NMF)**, **k-Nearest Neighbors (k-NN)**, **FAISS**, **ANNOY**, and **Autoencoders** for deeper insights into large-scale recommendations.
- **Explainable AI**: Each recommendation includes the similarity score and differences in attributes (e.g., danceability, energy) to help users understand why a particular song was chosen.

### 2. Data Fetching & Storage

- **Spotify API Integration**: Fetches track metadata and audio features (e.g., tempo, key, loudness) using the Spotify API.
- **MongoDB**: Stores track data, ensuring quick access to recommendations and reducing dependency on real-time API calls.
- **Redis**: Caches responses to reduce API calls and improve response times.


- **GitHub Actions**: Automates data fetching for missing information, processing 1,000 tracks at a time to stay within rate limits.


### 3. Background Jobs & Scalability

- Uses **Render Background Worker** for:
  - Fetching missing album images and audio features.
  - Periodically updating track information to ensure data freshness.
- An **uptime monitor** keeps the service active on the free tier of Render, preventing it from hibernating due to inactivity.

## 🔧 Technologies & Tools

- **Python & FastAPI**: For creating a fast, reliable backend.
- **Spotipy**: A lightweight Python library for accessing Spotify's Web API.
- **MongoDB**: Stores track data and user preferences.
- **Redis**: Improves performance with caching.
- **Pandas & BeautifulSoup**: For data preprocessing and web scraping.
- **SciKit-Learn**: For implementing machine learning algorithms.
- **Pytest**: For unit testing and ensuring code reliability.
- **Render**: A modern cloud platform for deploying the service.

## 📈 Future Improvements


- **NLP Integration**: Add sentiment analysis of lyrics to enhance the recommendations further, using libraries like **NLTK** or **spaCy**.

- **User Feedback Loop**: Allow users to rate recommendations and use this feedback to refine the recommendation algorithm.
- **Feature Expansion**: Include more user input options, such as allowing users to specify preferences like "I like the catchiness of this song" to shape recommendations further.

## 🌐 Deployed Service

- **API Base URL**: [recommendation-server-o85r.onrender.com](recommendation-server-o85r.onrender.com)


- **Live Demo**: [View a live demo of the Recommendation Engine](https://spotrec.vercel.app)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
