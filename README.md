# Movie Recommendation System

A production-ready REST API for movie recommendations using hybrid collaborative filtering and content-based recommendations via Flask and Docker.

## Overview

This project provides a Flask-based REST API that:

- Accepts user movie ratings as input
- Performs fuzzy matching to resolve movie titles
- Generates personalized movie recommendations using a hybrid approach
- Returns top 50 recommended movies with scores
- Caches processed data for fast subsequent requests

### Algorithm

The system uses a **hybrid recommendation approach** combining:

- **Content-based filtering (70%)**: Genre-based similarity scores
- **Collaborative filtering (30%)**: Similar user preferences

## Requirements

- **Docker**: 28.0 or above
- **Kagglehub API credentials** (free account at <https://www.kaggle.com>)

## Prerequisites

1. **Obtain Kagglehub credentials:**
   - Go to <https://www.kaggle.com/settings/account>.
   - Scroll to "API" section and click "Create New Token"
   - This downloads `kaggle.json` with your credentials

2. **Set up environment variables:**
   - Copy `.env.example` to `.env`
   - Open `.env` and fill in your Kagglehub credentials:

     ```sh
     KAGGLEHUB_USERNAME=your_kaggle_username
     KAGGLEHUB_API_KEY=your_api_key_here
     ```

## Setup

### Build the Docker image

```bash
docker compose build
```

### Run the container

```bash
docker compose up
```

On first startup, the container will:

1. Download movie and ratings data from Kagglehub (1-2 minutes)
1. Process and cache the data locally
1. Start the Flask API server on port 80

Subsequent startups will be faster (load from cache).

### Stop the container

```bash
docker compose down
```

## API

### GET /health

Returns 200 OK if the service is up.

### POST /recommendations

Generate movie recommendations based on user ratings.

### Input

The `/recommendations` endpoint enforces strict validation:

- **Ratings**: Must be a number between 1 and 5 (inclusive)
  - Invalid: `"Inception": 5.5` (out of range)
  - Invalid: `"Inception": "five"` (not a number)
  - Valid: `"Inception": 5` or `"Inception": 4.5`

- **Movie titles**: Must be non-empty strings, max 1023 characters
  - Invalid: `"": 5` (empty title)
  - Invalid: extremely_long_title...: 5` (>1023 chars)
  - Valid: `"Inception": 5`

- **Request body**: Must be a non-empty JSON object
  - Invalid: `{}` (empty)
  - Invalid: `["Inception", 5]` (array, not object)
  - Valid: `{"Inception": 5}`
