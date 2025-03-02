import requests
import pandas as pd
import time

# Your Guardian API key
GUARDIAN_API_KEY = "fef14378-9459-4ce6-b872-c53dee28d6f4"


def search_guardian_artist(artist, api_key, from_date="1900-01-01", to_date="2025-01-01", page_size=50, max_pages=2):
    """
    Searches The Guardian Content API for articles related to the given artist.
    The query is constructed to include the artist’s name in quotes plus the word "artist"
    to focus results on art-related content.

    :param artist: The artist's name (e.g. "Moise Kisling")
    :param api_key: Your Guardian API key.
    :param from_date: Start date for search.
    :param to_date: End date for search.
    :param page_size: Number of results per page.
    :param max_pages: How many pages of results to retrieve.
    :return: A list of article dictionaries.
    """
    endpoint = "https://content.guardianapis.com/search"
    all_articles = []

    # Construct query with quotes around the artist's name and add the term "artist"
    query = f'"{artist}" artist'

    for page in range(1, max_pages + 1):
        params = {
            "q": query,
            "from-date": from_date,
            "to-date": to_date,
            "api-key": api_key,
            "show-fields": "trailText,body",
            "page-size": page_size,
            "page": page,
            "order-by": "relevance",
            # Restrict to the culture section (optional)
            "section": "culture"
        }
        response = requests.get(endpoint, params=params)
        data = response.json()

        if "response" in data and "results" in data["response"]:
            results = data["response"]["results"]
            if not results:
                break  # No more articles for this artist
            for result in results:
                fields = result.get("fields", {})
                article_data = {
                    "id": result.get("id"),
                    "sectionName": result.get("sectionName", ""),
                    "webPublicationDate": result.get("webPublicationDate", ""),
                    "webTitle": result.get("webTitle", ""),
                    "webUrl": result.get("webUrl", ""),
                    "trailText": fields.get("trailText", ""),
                    "body": fields.get("body", "")
                }
                all_articles.append(article_data)
        else:
            break  # Unexpected response structure
    return all_articles


if __name__ == "__main__":
    # 1. Load your DataFrame of artists. Assume the CSV file has a column "artist"
    try:
        # Adjust the path/filename as needed.
        df_artists = pd.read_csv("final_df.csv")
    except Exception as e:
        print("Error reading CSV file:", e)
        exit(1)

    # 2. Get unique artist names
    unique_artists = df_artists["artist"].dropna().unique()
    print(f"Found {len(unique_artists)} unique artists.")

    results = []
    success_count = 0

    # 3. Iterate through each artist, and for each, try to get one relevant article.
    for artist in unique_artists:
        print(f"\nProcessing artist: {artist}")
        try:
            articles = search_guardian_artist(artist, GUARDIAN_API_KEY,
                                              from_date="1900-01-01",
                                              to_date="2025-01-01",
                                              page_size=50,
                                              max_pages=2)
            # Post-filter: Check if the article text actually mentions the artist (case-insensitive)
            relevant_articles = []
            for article in articles:
                combined_text = (article["webTitle"] + " " +
                                 article["trailText"] + " " +
                                 article["body"]).lower()
                if artist.lower() in combined_text:
                    relevant_articles.append(article)

            if relevant_articles:
                selected_article = relevant_articles[0]
                results.append({
                    "artist": artist,
                    "article_id": selected_article.get("id"),
                    "article_title": selected_article.get("webTitle"),
                    "publication_date": selected_article.get("webPublicationDate"),
                    "article_url": selected_article.get("webUrl"),
                    "snippet": selected_article.get("trailText")
                })
                print(
                    f"Found article for '{artist}': {selected_article.get('webTitle')}")
                success_count += 1
            else:
                results.append({
                    "artist": artist,
                    "article_id": None,
                    "article_title": None,
                    "publication_date": None,
                    "article_url": None,
                    "snippet": None,
                    "error": "No relevant article found"
                })
                print(f"No relevant article found for '{artist}'.")
        except Exception as e:
            results.append({
                "artist": artist,
                "article_id": None,
                "article_title": None,
                "publication_date": None,
                "article_url": None,
                "snippet": None,
                "error": str(e)
            })
            print(f"Error processing '{artist}': {e}")

        # Pause to avoid rate limits.
        time.sleep(1)

    # 4. Convert results to DataFrame and print summary.
    df_results = pd.DataFrame(results)
    total_artists = len(unique_artists)
    percentage = (success_count / total_artists) * 100 if total_artists else 0
    print(
        f"\nSummary: Found relevant articles for {success_count} out of {total_artists} artists ({percentage:.2f}%).")

    # 5. Save results to CSV
    df_results.to_csv("guardian_artist_articles.csv", index=False)
    print("Results saved to 'guardian_artist_articles.csv'.")
