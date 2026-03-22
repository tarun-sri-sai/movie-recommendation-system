import kagglehub
import os
import json
import shutil
import numpy as np
import pandas as pd
from collections import defaultdict
from pathlib import Path
from rapidfuzz import fuzz, process
from sklearn.preprocessing import MultiLabelBinarizer


class Recommender:
    def __init__(self):
        self.data_dir = Path("data")
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.movies_csv = self.data_dir / "movies.csv"
        self.ratings_csv = self.data_dir / "ratings.csv"
        self.cache_movies_json = self.cache_dir / "movies_processed.json"
        self.cache_metadata_json = self.cache_dir / "metadata.json"

        self.chunk_size = 100_000
        self.top_users_count = 10
        self.top_results_count = 50
        self.content_weight = 0.7
        self.collab_weight = 0.3

        self.movies_df = None
        self.genre_mappings = None
        self.movie_id_to_title = None
        self.movie_title_index = None
        self.ratings_dtype = {
            "userId": np.int32,
            "movieId": np.int32,
            "rating": np.float16,
            "timestamp": np.int32
        }

        self._load_or_cache_data()

    def _load_or_cache_data(self):
        if (
            self.cache_movies_json.exists() and
            self.cache_metadata_json.exists()
        ):
            self._load_from_cache()
        else:
            self._download_and_cache_data()

    def _download_and_cache_data(self):
        if not any(self.data_dir.iterdir()):
            dataset_path = kagglehub.dataset_download(
                "parasharmanas/movie-recommendation-system"
            )

            for item in os.listdir(dataset_path):
                src = os.path.join(dataset_path, item)
                dst = self.data_dir / item
                if dst.exists():
                    dst.unlink()
                shutil.move(src, str(dst))

        self._process_and_cache_data()

    def _process_and_cache_data(self):
        movies_df = pd.read_csv(
            self.movies_csv,
            dtype={"movieId": np.int32, "title": str, "genres": str}
        )
        movies_df = movies_df.dropna()

        mlb = MultiLabelBinarizer()
        encodings = mlb.fit_transform(movies_df["genres"].str.split("|"))
        genre_bits = np.zeros(len(movies_df), dtype=np.int32)
        for i in range(encodings.shape[1]):
            genre_bits = genre_bits | (encodings[:, i].astype(np.int32) << i)

        movies_df["genres"] = genre_bits

        genre_mappings = dict(zip(movies_df["movieId"], movies_df["genres"]))
        movie_id_to_title = dict(zip(movies_df["movieId"], movies_df["title"]))

        self.movies_df = movies_df
        self.genre_mappings = genre_mappings
        self.movie_id_to_title = movie_id_to_title

        self.movie_title_index = list(movie_id_to_title.values())

        cache_data = {
            "movies_df": movies_df.to_dict(orient="list"),
            "genre_mappings": {
                str(k): int(v) for k, v in genre_mappings.items()
            },
            "movie_id_to_title": {
                str(k): v for k, v in movie_id_to_title.items()
            },
            "movie_title_index": self.movie_title_index
        }
        with open(self.cache_movies_json, "w") as f:
            json.dump(cache_data, f)

    def _load_from_cache(self):
        with open(self.cache_movies_json, "r") as f:
            cached_data = json.load(f)
            self.movies_df = pd.DataFrame(cached_data["movies_df"])
            self.genre_mappings = {
                int(k): int(v) for k, v in cached_data["genre_mappings"].items()
            }
            self.movie_id_to_title = {
                int(k): v for k, v in cached_data["movie_id_to_title"].items()}
            self.movie_title_index = cached_data["movie_title_index"]

    def _fuzzy_match_title(self, query):
        if not query or not isinstance(query, str):
            raise ValueError("Movie title must be a non-empty string")

        matches = process.extractOne(
            query, self.movie_title_index, scorer=fuzz.WRatio)
        if not matches or matches[1] < 50:
            raise ValueError(f"No suitable movie match found for '{query}'")

        matched_title = matches[0]
        for movie_id, title in self.movie_id_to_title.items():
            if title == matched_title:
                return movie_id
        raise ValueError(f"Could not resolve title '{query}' to movie ID")

    def _read_ratings_in_chunks(self):
        reader = pd.read_csv(
            self.ratings_csv,
            chunksize=self.chunk_size,
            dtype=self.ratings_dtype
        )
        for chunk in reader:
            yield chunk.dropna()

    def _compute_content_scores(self, user_movie_ids):
        genre_strengths = defaultdict(int)
        for movie_id in user_movie_ids:
            for i in range(32):
                genre_strengths[i] += (
                    (self.genre_mappings[movie_id] >> i) & 1
                )

        genre_similarities = defaultdict(float)
        for movie_id, movie_genres in self.genre_mappings.items():
            for user_movie_id in user_movie_ids:
                common = self.genre_mappings[user_movie_id] & movie_genres
                for i in range(32):
                    genre_similarities[movie_id] += (
                        ((common >> i) & 1) * genre_strengths[i]
                    )

        max_score = (
            max(genre_similarities.values())
            if genre_similarities
            else 1
        )
        genre_similarities = {
            k: v / max_score for k, v in genre_similarities.items()
        }

        return dict(genre_similarities)

    def _compute_collaborative_scores(self, user_movie_ids):
        user_scores = defaultdict(float)
        user_counts = defaultdict(int)

        for chunk in self._read_ratings_in_chunks():
            chunk_fil = chunk[chunk["movieId"].isin(user_movie_ids)].copy()
            if chunk_fil.empty:
                continue

            for _, row in chunk_fil.iterrows():
                user_scores[row["userId"]] += 1
                user_counts[row["userId"]] += 1

        user_similarities = [
            (int(u), user_scores[u]) for u in user_scores if user_counts[u] > 0
        ]
        top_users = dict(
            sorted(user_similarities, key=lambda x: x[1], reverse=True)[
                :self.top_users_count
            ]
        )

        if not top_users:
            return {}

        movie_scores = defaultdict(float)
        movie_counts = defaultdict(int)

        for chunk in self._read_ratings_in_chunks():
            chunk_fil = chunk[chunk["userId"].isin(top_users)].copy()
            if chunk_fil.empty:
                continue

            for _, row in chunk_fil.iterrows():
                movie_scores[row["movieId"]] += row["rating"]
                movie_counts[row["movieId"]] += 1

        similar_movie_scores = {
            int(m): movie_scores[m] / movie_counts[m]
            for m in movie_scores
            if movie_counts[m] > 0
        }

        if not similar_movie_scores:
            return {}

        max_scores = max(similar_movie_scores.values())
        similar_movie_scores = {
            k: v / max_scores for k, v in similar_movie_scores.items()
        }

        return similar_movie_scores

    def get_recommendations(self, user_ratings):
        if not user_ratings:
            raise ValueError("User ratings cannot be empty")

        user_movie_ids = []
        for title in user_ratings.keys():
            try:
                movie_id = self._fuzzy_match_title(title)
                user_movie_ids.append(movie_id)
            except ValueError as e:
                raise ValueError(f"Invalid movie title '{title}': {str(e)}")

        if not user_movie_ids:
            raise ValueError("No valid movies found in ratings")

        genre_scores = self._compute_content_scores(user_movie_ids)

        collab_scores = self._compute_collaborative_scores(user_movie_ids)

        final_scores = []
        for movie_id, content_score in genre_scores.items():
            collab_score = collab_scores.get(movie_id, 0)
            final_score = (
                self.content_weight * content_score +
                self.collab_weight * collab_score
            )
            movie_title = self.movie_id_to_title.get(movie_id)
            if movie_title:
                final_scores.append((movie_title, final_score))

        final_scores.sort(key=lambda x: x[1], reverse=True)
        top_recommendations = final_scores[:self.top_results_count]

        result = {title: score for title, score in top_recommendations}
        return result
