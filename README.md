# 📚 Recommendation Engine — Books (Open Library)

This service powers **book recommendations** using the [Open Library API](https://openlibrary.org/developers/api) and MongoDB. It recommends books similar to a chosen title using cosine similarity on metadata-derived features (e.g. subject count, author count).

**Migration note:** The app was migrated from Spotify (tracks) to Open Library (books). Track-based recommendations remain available only when data already exists in MongoDB; no new Spotify fetching. See `MIGRATION_AND_ARCHITECTURE.md` and `MIGRATION_CHECKPOINT.md`.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/render-examples/fastapi)

## 🌟 Features

- **Book recommendations**: `GET /recommendations/books/cosine-similarity/{work_id}` — suggests books similar to a given Open Library work using features like subject count, author count, and cover count.
- **Explainable recommendations**: Each recommendation includes a similarity score and feature differences.
- **Open Library integration**: Fetches work metadata (and author name) from Open Library when a book is not yet in MongoDB, then stores it for future similarity queries.
- **Legacy track endpoint**: `GET /recommendations/cosine-similarity/{track_id}` still works if the track exists in MongoDB (no Spotify API calls).

## 📚 Overview & Purpose

This project was driven by a curiosity to understand the mechanics behind recommendation engines, including both traditional machine learning and deep learning approaches. It serves as an exploration of balancing **recommendation accuracy** and **explainability** with **engineering considerations** like processing time, file sizes, and data shapes. The goal is to provide meaningful recommendations with insights that users can trust.

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+**
- **MongoDB Atlas** (or any MongoDB): Connection string for storing book metadata. See `ENV.md` and `.env.example`.
- **Render Account** (optional): For deploying the service.

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

4. Create a `.env` file (see `.env.example` and `ENV.md`):

   ```
   MONGO_URL=your_mongodb_connection_string
   SECRET_TOKEN=your_secret_token
   ```
   Optional: `OPEN_LIBRARY_USER_AGENT`, `OPEN_LIBRARY_CONTACT_EMAIL` for Open Library rate limits.

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

### Book recommendations

1. Client calls `GET /recommendations/books/cosine-similarity/{work_id}?token=...`.
2. Server looks up the work in MongoDB (`Books.books_with_metadata`). If missing or incomplete, it fetches the work (and author name) from the Open Library API and inserts the document.
3. Cosine similarity is computed over numeric features: `author_count`, `subject_count`, `cover_count`.
4. Response returns the top similar books with similarity scores and feature differences.

### Data & storage

- **MongoDB**: `Books.books_with_metadata` stores book documents (work_id, title, author_name, subject_count, etc.). Legacy `Tracks.tracks_with_features` is still used only for the track endpoint when data exists.
- **Open Library API**: Used to fetch work and author metadata on demand. Identify requests with `User-Agent` (and optional contact email) for better rate limits.

## 🔧 Technologies & Tools

- **Python & FastAPI**: Backend API.
- **MongoDB**: Stores book (and legacy track) metadata.
- **Open Library API**: Source for work and author metadata.
- **SciKit-Learn**: Cosine similarity for recommendations.
- **Pytest**: Unit tests.
- **Render**: Optional deployment.

## 📈 Future Improvements


- **NLP Integration**: Add sentiment analysis of lyrics to enhance the recommendations further, using libraries like **NLTK** or **spaCy**.

- **User Feedback Loop**: Allow users to rate recommendations and use this feedback to refine the recommendation algorithm.
- **Feature Expansion**: Include more user input options, such as allowing users to specify preferences like "I like the catchiness of this song" to shape recommendations further.

## 🌐 Deployed Service

- **API Base URL**: [recommendation-server-o85r.onrender.com](recommendation-server-o85r.onrender.com)


- **Live Demo**: [View a live demo of the Recommendation Engine](https://spotrec.vercel.app)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
