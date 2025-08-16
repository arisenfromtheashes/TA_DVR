import json
import os
import requests

# Configuration
BASE_URL = "http://{IP_ADDRESS}:8000/api" . # Replace with your TA server IP address
VIDEO_ENDPOINT = f"{BASE_URL}/video/"
WATCHED_ENDPOINT = f"{BASE_URL}/watched/"
TOKEN = "{TOKEN}"  # Replace with your actual token
HEADERS = {"Authorization": f"Token {TOKEN}"}
SELECTED_CHANNELS_FILE = "./selected_channels.json"

def load_selected_channels():
    """Load selected channels from JSON file."""
    if not os.path.exists(SELECTED_CHANNELS_FILE):
        print(f"Error: {SELECTED_CHANNELS_FILE} not found.")
        return []
    
    try:
        with open(SELECTED_CHANNELS_FILE, 'r') as f:
            channels = json.load(f)
        # Validate and deduplicate channels
        seen_ids = set()
        valid_channels = []
        for ch in channels:
            channel_id = ch.get('channel_id')
            if not channel_id or not ch.get('channel_name'):
                print(f"Warning: Skipping invalid channel entry: {ch}")
                continue
            if channel_id in seen_ids:
                print(f"Warning: Duplicate channel ID {channel_id}: {ch['channel_name']}")
                continue
            seen_ids.add(channel_id)
            valid_channels.append(ch)
        
        print(f"Loaded {len(valid_channels)} channels from {SELECTED_CHANNELS_FILE}:")
        for ch in valid_channels:
            print(f"  - {ch['channel_name']} ({ch['channel_id']})")
        return valid_channels
    except Exception as e:
        print(f"Error reading {SELECTED_CHANNELS_FILE}: {e}")
        return []

def fetch_all_pages(endpoint):
    """Fetch all paginated results from a given API endpoint."""
    all_data = []
    page = 0
    while True:
        url = f"{endpoint}?page={page}"
        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            json_data = response.json()
            data = json_data.get("data", [])
            paginate = json_data.get("paginate", {})
            all_data.extend(data)
            if not paginate or page >= paginate.get("last_page", 0):
                break
            page += 1
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            break
    return all_data

def fetch_videos():
    """Fetch all videos from API."""
    return fetch_all_pages(VIDEO_ENDPOINT)

def mark_video_watched(video_id):
    """Send POST request to mark a video as watched."""
    payload = {
        "id": video_id,
        "is_watched": True
    }
    try:
        response = requests.post(WATCHED_ENDPOINT, headers=HEADERS, json=payload)
        response.raise_for_status()
        print(f"Marked video {video_id} as watched.")
        return True
    except requests.RequestException as e:
        print(f"Error marking video {video_id} as watched: {e}")
        return False

def main():
    """Read selected channels, fetch videos, and mark unwatched videos as watched."""
    # Load selected channels
    selected_channels = load_selected_channels()
    if not selected_channels:
        print("No selected channels. Exiting.")
        return
    
    selected_ids = {ch['channel_id'] for ch in selected_channels}
    print(f"Processing videos for {len(selected_ids)} selected channels.")
    
    # Fetch all videos
    videos = fetch_videos()
    if not videos:
        print("No videos fetched. Exiting.")
        return
    
    # Filter videos to selected channels and process
    processed = 0
    marked = 0
    for video in videos:
        channel_obj = video.get("channel", {})
        channel_id = channel_obj.get("channel_id")
        if channel_id not in selected_ids:
            continue
        
        # Get video ID (use youtube_id)
        video_id = video.get('youtube_id')
        if not video_id:
            print(f"Skipping video with missing youtube_id: {video.get('title', 'Untitled')}")
            print(f"Video object: {json.dumps(video, indent=2)}")
            continue
        
        # Check watched status
        watched = video.get("player", {}).get("watched", False)
        if watched:
            print(f"Video {video_id} already watched: {video.get('title', 'Untitled')}")
        else:
            if mark_video_watched(video_id):
                marked += 1
        processed += 1
    
    print(f"\nProcessed {processed} videos from selected channels.")
    print(f"Marked {marked} videos as watched.")

if __name__ == "__main__":
    main()
