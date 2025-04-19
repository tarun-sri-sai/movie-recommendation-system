# Movie Recommendation System

## Approach

### 1. Preparing the movie data

1. Load the movie data from the file "movies.csv" consisting of the columns `movieId`, `title`, and `genres` into the dataframe `movies_df`.
2. Drop the rows with missing values.
3. One-hot encode the `genres` column by splitting with "|".
4. Store the one-hot encodings back into the `genres` column by encoding them as 32-bit integers (since we have less than 32 genres).

### 2. Preparing the input data

1. Load the movie data from the file "input.csv" consisting of the columns `movieId`, `title` and `rating` into the dataframe `input_df`.
2. Drop the rows with missing values.
3. Drop the rows whose `movieId` is not present in `movies_df`.

### 3. Content-based filtering

1. Pre-compute the `genre_mappings`:
   1. Define a dictionary called `genre_mappings`.
   2. For each movie in `movies_df`, add the (`movieId`, `genres`) pair to `genre_mappings`.
2. Pre-compute the `genre_strengths`:
   1. Define a dictionary called `genre_strengths`.
   2. Use the `genre_mappings` to get the `genres` of each movie in `input_df` and add the number of times each genre appears in `input_df` into `genre_strengths`.
3. Compute the genre similarity scores:
   1. Define a dictionary called `genre_similarities`.
   2. For each movie in `movies_df`, the genre similarity score of the movie is the sum of the genres that are present in `genre_strengths` multiplied by the strength value of that genre.
4. Normalize the `genre_similarities` in the range 0 to 1.

### 4. Preparing the rating data

1. Load the movie data from the file "ratings.csv" consisting of the columns `userId`, `movieId`, `rating`, `timestamp` into the dataframe `ratings_df`.
2. Pre-compute the `rating_mappings`:
   1. Define a dictionary called `rating_mappings`.
   2. For each row in `input_df`, add the (`movieId`, `rating`) pairs into `rating_mappings`.

### 5. Collaborative filtering

1. Compute the user similarity scores:
   1. Define two dictionaries called `user_scores` and `user_counts`.
   2. For each row in `ratings_df` filtered by `movieId` present in the `rating_mappings`:
      1. Calculate the inverse mean absolute error of the user given rating for the movie and the rating in the row.
      2. Add it to the `user_scores` with the key as `userId`.
      3. Increment the count in `user_counts` by 1 for each row added with the key as `userId`.
   3. Define a list of lists called `user_similarities`.
   4. For each user in `user_scores` if the value in `user_counts` is greater than 0:
      1. Add a pair containing the `userId` followed by the value for the user in `user_scores`.
2. Get the top 10 users from the `user_similarities` and put them in `top_users`.
3. Compute the scores for movies rated by users in `top_users`:
   1. Define two dictionaries called `movie_ratings` and `movie_counts`.
   2. For each row in `ratings_df` filtered by `userId` present in the `top_users`:
      1. Add the `rating` to the `movie_ratings` with the key as `movieId`.
      2. Increment the count in `movie_counts` by 1 for each row added with the key as `userId`.
   3. Define a dict called `similar_movie_scores`.
   4. For each movie in `movie_ratings` if the value in `movie_counts` is greater than 0:
      1. Add the average rating computed by dividing the value for the movie in `movie_ratings` with the value in `movie_counts` with the key as `movieId`.
4. Normalize the `similar_movie_scores` in the range 0 to 1.

### 6. Final result

1. Compute the final result:
   1. Define a list of lists called `final_scores`.
   2. For each `movieId` in `genre_similarities`:
      1. Add a pair containing the `movieId` followed by the average of the value in `genre_similarities` and the value in `similar_movie_scores`.
2. Get the top 50 movies from the `final_scores` and store them in `top_movies`.
