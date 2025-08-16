import json
import requests
from collections import defaultdict

# Configuration
BASE_URL = "http://{IP_ADDRESS}:8000/api" . # Replace with your TA server IP address
CHANNEL_ENDPOINT = f"{BASE_URL}/channel/"
VIDEO_ENDPOINT = f"{BASE_URL}/video/"
WATCHED_ENDPOINT = f"{BASE_URL}/watched/"
TOKEN = "{TOKEN}"  # Replace with your actual token
HEADERS = {"Authorization": f"Token {TOKEN}"}

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

def fetch_channels():
    """Fetch all channels from API and deduplicate by channel_id."""
    channels = fetch_all_pages(CHANNEL_ENDPOINT)
    seen_ids = set()
    deduped_channels = []
    for channel in channels:
        channel_id = channel.get('channel_id')
        if channel_id and channel_id not in seen_ids:
            seen_ids.add(channel_id)
            deduped_channels.append(channel)
    return deduped_channels

def fetch_videos():
    """Fetch all videos from API."""
    return fetch_all_pages(VIDEO_ENDPOINT)

def mark_videos_unwatched(channel_id, videos):
    """Send POST requests to mark all videos of a channel as unwatched."""
    marked = 0
    for video in videos:
        channel_obj = video.get("channel", {})
        if channel_obj.get("channel_id") != channel_id:
            continue
        video_id = video.get('youtube_id')
        if not video_id:
            print(f"Skipping video with missing youtube_id: {video.get('title', 'Untitled')}")
            continue
        payload = {
            "id": video_id,
            "is_watched": False
        }
        try:
            response = requests.post(WATCHED_ENDPOINT, headers=HEADERS, json=payload)
            response.raise_for_status()
            print(f"Marked video {video_id} as unwatched: {video.get('title', 'Untitled')}")
            marked += 1
        except requests.RequestException as e:
            print(f"Error marking video {video_id} as unwatched: {e}")
    return marked

def display_channel_video_report(channels, videos):
    """Display sorted channels with watched/unwatched video counts and videos."""
    # Organize videos by channel and count watched/unwatched
    videos_by_channel = defaultdict(list)
    watched_counts = defaultdict(int)
    unwatched_counts = defaultdict(int)
    for video in videos:
        channel_obj = video.get("channel", {})
        channel_id = channel_obj.get("channel_id")
        if channel_id:
            videos_by_channel[channel_id].append(video)
            watched = video.get("player", {}).get("watched", False)
            if watched:
                watched_counts[channel_id] += 1
            else:
                unwatched_counts[channel_id] += 1
    
    # Filter channels with videos and sort by name
    channel_lookup = {c['channel_id']: c['channel_name'] for c in channels}
    sorted_channels = sorted(
        [(cid, vids) for cid, vids in videos_by_channel.items()],
        key=lambda x: channel_lookup.get(x[0], "Unknown Channel").lower()
    )
    
    if not sorted_channels:
        print("No channels with videos.")
        return
    
    for channel_id, vids in sorted_channels:
        channel_name = channel_lookup.get(channel_id, "Unknown Channel")
        watched = watched_counts[channel_id]
        unwatched = unwatched_counts[channel_id]
        sorted_vids = sorted(
            vids,
            key=lambda v: v.get("published", "9999-12-31"),
            reverse=True
        )
        print(f"\nChannel: {channel_name} (ID: {channel_id}, Watched: {watched}, Unwatched: {unwatched})")
        for v in sorted_vids:
            watched = v.get("player", {}).get("watched", False)
            title = v.get("title", "Untitled")
            vid_type = v.get("vid_type", "Unknown")
            published = v.get("published", "Unknown")
            date = published.split('T')[0] if published and 'T' in published else published
            video_id = v.get('youtube_id', '')
            video_id_display = f" ({video_id})" if video_id else ""
            print(f"  - [{'x' if watched else ' '}] {vid_type}: {title}{video_id_display} [{date}]")

def display_channels(channels, videos):
    """Display channels with watched/unwatched video counts."""
    # Count watched/unwatched videos per channel
    watched_counts = defaultdict(int)
    unwatched_counts = defaultdict(int)
    for video in videos:
        channel_obj = video.get("channel", {})
        channel_id = channel_obj.get("channel_id")
        if channel_id:
            watched = video.get("player", {}).get("watched", False)
            if watched:
                watched_counts[channel_id] += 1
            else:
                unwatched_counts[channel_id] += 1
    
    sorted_channels = sorted(channels, key=lambda x: x['channel_name'].lower())
    print("\n=== Channel Selection ===")
    for i, channel in enumerate(sorted_channels, 1):
        channel_id = channel['channel_id']
        watched = watched_counts.get(channel_id, 0)
        unwatched = unwatched_counts.get(channel_id, 0)
        print(f"{i}. {channel['channel_name']} ({channel_id}, Watched: {watched}, Unwatched: {unwatched})")
    print("Enter the number of a channel to mark all videos as unwatched, or 'q' to quit.")

def main():
    """Main function to display report, manage menu, and mark videos unwatched."""
    while True:
        # Fetch channels and videos
        channels = fetch_channels()
        if not channels:
            print("No channels fetched. Exiting.")
            return
        
        videos = fetch_videos()
        
        # Display report
        print("\n=== Channel and Video Report ===")
        display_channel_video_report(channels, videos)
        
        # Display menu and handle selection
        display_channels(channels, videos)
        choice = input("Choice: ").strip().lower()
        
        if choice == 'q':
            print("Exiting.")
            break
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(channels):
                channel = sorted(channels, key=lambda x: x['channel_name'].lower())[index]
                channel_id = channel['channel_id']
                channel_name = channel['channel_name']
                print(f"Marking all videos as unwatched for {channel_name}...")
                marked = mark_videos_unwatched(channel_id, videos)
                print(f"Marked {marked} videos as unwatched for {channel_name}.")
            else:
                print("Invalid index.")
        except ValueError:
            print("Please enter a valid number or 'q'.")

if __name__ == "__main__":
    main()
