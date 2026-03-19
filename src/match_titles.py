import pandas as pd
from pathlib import Path
from rapidfuzz import process, fuzz


class MovieIndex:
    def __init__(self):
        self._movies = None

        self.fetch_movies()

    def fetch_movies(self):
        movies = pd.read_csv(Path("data") / "movies.csv")

        self._movies = {
            title: movieId
            for title, movieId in zip(
                movies["title"].tolist(),
                movies["movieId"].tolist()
            )
        }

    def search(self, query):
        movie_titles = list(self._movies.keys())

        matches = process.extractOne(query, movie_titles, scorer=fuzz.WRatio)
        return self._movies[matches[0]]


def main():
    try:
        index = MovieIndex()
    except Exception as e:
        print(f"Please make sure to download the dataset. Error: {e}")

    try:
        input_file = Path("data") / "input.csv"
        input_data = pd.read_csv(input_file)
        input_data["movieId"] = input_data["title"].apply(index.search)
        input_data.to_csv(input_file, index=False)
    except Exception as e:
        print(f"Please add movie ratings to {input_file}. Error: {e}")


if __name__ == "__main__":
    main()
