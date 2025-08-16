import json
import os
import requests
from collections import defaultdict

# Configuration
BASE_URL = "http://{IPADDRESS}:8000/api"  # Replace with you TA server IP address
CHANNEL_ENDPOINT = f"{BASE_URL}/channel/"
VIDEO_ENDPOINT = f"{BASE_URL}/video/"
TOKEN = "{TOKEN}"  # Replace with your actual token
HEADERS = {"Authorization": f"Token {TOKEN}"}
SELECTED_CHANNELS_FILE = "./selected_channels.json"

def load_selected_channels():
    """Load selected channel IDs from JSON file."""
    if os.path.exists(SELECTED_CHANNELS_FILE):
        try:
            with open(SELECTED_CHANNELS_FILE, 'r') as f:
                channels = json.load(f)
            return {ch['channel_id'] for ch in channels if ch.get('channel_id')}
        except Exception as e:
            print(f"Error reading {SELECTED_CHANNELS_FILE}: {e}")
    return set()

def save_selected_channels(selected_channel_ids, all_channels):
    """Save selected channels to JSON file, sorted by channel_id."""
    # Build selected channels list from IDs and all_channels
    channel_lookup = {c['channel_id']: c['channel_name'] for c in all_channels}
    selected_channels = [
        {"channel_id": cid, "channel_name": channel_lookup.get(cid, "Unknown Channel")}
        for cid in sorted(selected_channel_ids)
        if cid in channel_lookup
    ]
    try:
        with open(SELECTED_CHANNELS_FILE, 'w') as f:
            json.dump(selected_channels, f, indent=2)
        print(f"Saved {len(selected_channels)} channels to {SELECTED_CHANNELS_FILE}")
    except Exception as e:
        print(f"Error writing {SELECTED_CHANNELS_FILE}: {e}")

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
    # Deduplicate channels by channel_id, keeping first occurrence
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

def display_channel_video_report(channels, videos):
    """Display sorted channels with video counts and date-sorted videos."""
    selected_channel_ids = load_selected_channels()
    
    # Organize videos by channel
    videos_by_channel = defaultdict(list)
    for video in videos:
        channel_obj = video.get("channel", {})
        channel_id = channel_obj.get("channel_id")
        if channel_id and channel_id in selected_channel_ids:
            videos_by_channel[channel_id].append(video)
    
    # Filter channels to selected only and sort by name
    channel_lookup = {c['channel_id']: c['channel_name'] for c in channels}
    sorted_channels = sorted(
        [(cid, vids) for cid, vids in videos_by_channel.items() if cid in selected_channel_ids],
        key=lambda x: channel_lookup.get(x[0], "Unknown Channel").lower()
    )
    
    if not sorted_channels:
        print("No selected channels with videos.")
        return
    
    for channel_id, vids in sorted_channels:
        channel_name = channel_lookup.get(channel_id, "Unknown Channel")
        sorted_vids = sorted(
            vids,
            key=lambda v: v.get("published", "9999-12-31"),
            reverse=True
        )
        print(f"\nChannel: {channel_name} (ID: {channel_id}, Videos: {len(sorted_vids)})")
        for v in sorted_vids:
            watched = v.get("player", {}).get("watched", False)
            title = v.get("title", "Untitled")
            vid_type = v.get("vid_type", "Unknown")
            published = v.get("published", "Unknown")
            date = published.split('T')[0] if published and 'T' in published else published
            # Try 'youtube_id', 'id', or 'video_id' for video ID, omit if missing
            video_id = v.get('youtube_id') or v.get('id') or v.get('video_id', '')
            video_id_display = f" ({video_id})" if video_id else ""
            print(f"  - [{'x' if watched else ' '}] {vid_type}: {title}{video_id_display} [{date}]")

def display_channels(channels, videos, selected_channel_ids):
    """Display channels with selection status and video counts."""
    # Count videos per channel
    video_counts = defaultdict(int)
    for video in videos:
        channel_obj = video.get("channel", {})
        channel_id = channel_obj.get("channel_id")
        if channel_id:
            video_counts[channel_id] += 1
    
    sorted_channels = sorted(channels, key=lambda x: x['channel_name'].lower())
    for i, channel in enumerate(sorted_channels, 1):
        status = '[x]' if channel['channel_id'] in selected_channel_ids else '[ ]'
        video_count = video_counts.get(channel['channel_id'], 0)
        print(f"{i}. {status} {channel['channel_name']} ({channel['channel_id']}, Videos: {video_count})")

def toggle_channel_selection(channels, selected_channel_ids, choice):
    """Toggle channel selection by index and rewrite selected_channels.json."""
    sorted_channels = sorted(channels, key=lambda x: x['channel_name'].lower())
    try:
        index = int(choice) - 1
        if 0 <= index < len(sorted_channels):
            channel = sorted_channels[index]
            channel_id = channel['channel_id']
            channel_name = channel['channel_name']
            
            if channel_id in selected_channel_ids:
                selected_channel_ids.remove(channel_id)
                print(f"Unselected {channel_name}")
            else:
                selected_channel_ids.add(channel_id)
                print(f"Selected {channel_name}")
            
            # Rewrite selected_channels.json with current selections
            save_selected_channels(selected_channel_ids, channels)
            return selected_channel_ids
        else:
            print("Invalid index")
    except ValueError:
        print("Please enter a valid number")
    return selected_channel_ids

def main():
    """Main function to display channel/video report and manage channels."""
    channels = fetch_channels()
    if not channels:
        print("No channels fetched. Exiting.")
        return
    
    selected_channel_ids = load_selected_channels()
    videos = fetch_videos()
    
    print("\n=== Channel and Video Report ===")
    display_channel_video_report(channels, videos)
    
    while True:
        print("\n=== Channel Selection ===")
        display_channels(channels, videos, selected_channel_ids)
        print("\nEnter the number of a channel to toggle selection, or 'q' to quit.")
        choice = input("Choice: ").strip()
        if choice.lower() == 'q':
            break
        selected_channel_ids = toggle_channel_selection(channels, selected_channel_ids, choice)

if __name__ == "__main__":
    main()
