import requests
import pandas as pd
import time

# Your Artsy API credentials
CLIENT_ID = "22f1f33bdb34a46de7a0"
CLIENT_SECRET = "e4bc5306a7a627bed1a9fcc7814d4e7c"


def get_artsy_token(client_id, client_secret):
    """
    Obtain an Xapp token from Artsy's API.
    """
    token_url = "https://api.artsy.net/api/tokens/xapp_token"
    params = {"client_id": client_id, "client_secret": client_secret}
    response = requests.post(token_url, params=params)
    response.raise_for_status()  # Raise an error if the request fails
    token = response.json().get("token")
    return token


def search_artsy_artist(artist_name, token):
    """
    Search for an artist by name using Artsy's search endpoint.
    Uses parameter 'q' with type 'artist'.
    Returns the first matching artist's Artsy ID.
    """
    search_url = "https://api.artsy.net/api/search"
    headers = {
        "X-Xapp-Token": token,
        "Accept": "application/vnd.artsy-v2+json"
    }
    params = {
        "q": artist_name,
        "type": "artist"
    }
    response = requests.get(search_url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    results = data.get("response", {}).get("results", [])
    if not results:
        return None
    # Assume the first result is the correct artist.
    return results[0].get("id")


def get_artist_info(artist_id, token):
    """
    Retrieve full artist information from Artsy's artist endpoint.
    """
    artist_endpoint = f"https://api.artsy.net/api/artists/{artist_id}"
    headers = {
        "X-Xapp-Token": token,
        "Accept": "application/vnd.artsy-v2+json"
    }
    response = requests.get(artist_endpoint, headers=headers)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    # 1. Obtain an Artsy token
    token = get_artsy_token(CLIENT_ID, CLIENT_SECRET)
    print("Xapp token obtained:")
    print(token)

    # 2. Read your CSV file containing artist names.
    # Assume the CSV file is named 'artists.csv' and has a column called "artist".
    try:
        df_artists = pd.read_csv("final_df.csv")
    except Exception as e:
        print("Error reading CSV file:", e)
        exit(1)

    # 3. Get unique artist names from the DataFrame
    unique_artists = df_artists["artist"].dropna().unique()
    print(f"Found {len(unique_artists)} unique artists in the CSV.")

    results = []
    successful = 0  # Count how many artists yielded data

    # 4. Iterate over each unique artist and fetch their Artsy data.
    for artist in unique_artists:
        print(f"Processing artist: {artist}")
        try:
            artsy_id = search_artsy_artist(artist, token)
            if not artsy_id:
                results.append({
                    "artist": artist,
                    "artsy_id": None,
                    "name": None,
                    "birthday": None,
                    "hometown": None,
                    "biography": None,
                    "error": "Artist not found"
                })
                print(f"Artist not found for '{artist}'.")
                continue
            artist_info = get_artist_info(artsy_id, token)
            results.append({
                "artist": artist,
                "artsy_id": artsy_id,
                "name": artist_info.get("name"),
                "birthday": artist_info.get("birthday"),
                "hometown": artist_info.get("hometown"),
                "biography": artist_info.get("biography")
            })
            print(f"Found data for '{artist}': {artist_info.get('name')}")
            successful += 1
        except Exception as e:
            results.append({
                "artist": artist,
                "artsy_id": None,
                "name": None,
                "birthday": None,
                "hometown": None,
                "biography": None,
                "error": str(e)
            })
            print(f"Error processing artist '{artist}': {e}")
        # Sleep a bit to avoid hitting rate limits.
        time.sleep(1)

    # 5. Create a DataFrame with the results.
    df_results = pd.DataFrame(results)

    total = len(unique_artists)
    percentage = (successful / total) * 100 if total > 0 else 0
    print(
        f"\nSummary: Found data for {successful} out of {total} artists ({percentage:.2f}%).")

    # 6. Save the results to a CSV file.
    df_results.to_csv("artsy_artist_info.csv", index=False)
    print("Results saved to 'artsy_artist_info.csv'.")
