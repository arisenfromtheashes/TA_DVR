# **TA_DVR**
Scripts to assist in using Tube Archivist like a DVR

## <ins>**Preface:**</ins> 
These help under a specific set of circumstances. I feel I must explain how I use TA. 
Currently I archive several channels, but some I wish to archive in perpetuity, while others, I just want to dodge ads to watch and then let the built in TA functionality remove. If you use the built in functionality in TA to remove episodes, it only works if in TA they are marked as watched. Heres where these scripts help my specific use case. I watch in Plex, which currently syncs videos across. but not watch status (without large workarounds and additonal software). So what these scripts do is this:

<ins>getytvideos.py:</ins> Connects to my TA instance, gets a list of all channels and their archived videos with watched status a and spits out their information just to see, then at the bottom it gives a list of each and every channel with a 'markable' box next to it. Using arrow keys and enter key, you can mark channels you wish to be 'selected' to have their videos marked as watched on a regular basis using the next script. Once done, this script spits out a json file listing the 'selected' channels to be used by the next script to mark watched. 

<ins>mark_videos_watched.py:</ins> This is the script I set on a schedule to mark the 'selected' channels' videos marked watched. Daily is enough for me. This script connects to my TA instance, grabs the json file the first script created, and for each of those channels, marks their respective videos as watched, allowing the built in TA functionality to remove the watched videos. I have this set to run daily via a cron job.

<ins>**NOTE**:</ins> This requires you to already have set, for each of your selected channel(s), the setting in TA to delete watched videos after x days. For me this works great. I have channels I want to archive in perpetuity have that TA setting disabled, and the others, I have set to 21 days. What this means in my setup is that I have 21 days to watch new content on my 'selected' channels, period, before it wont be in Plex or TA anymore because my automation marks them watched daily. This is fine for me. If I dont watch it in 3 weeks, Im likely not to.

For testing and refining purposes, I needed to be able to test marking videos watched over and over. Rather than unmarking them manually, I created a script to unmark as watched too. 

<ins>mark_videos_watched.py:</ins> This script will connect to my TA intance, get a list of all channels and their archived videos with watched status a and spits out their information just to see, then at the bottom it gives a list of each and every channel with a 'markable' box next to it. Using arrow keys and enter key, you can select channels you wish to mark all videos unwatched. This allows quick marking of multitudes of videos back and forth with the previous scripts and this one.


The only thing you need for these scripts is network access to your TA instance, python3, the location they are in to have write permissions (for the json file) and you need to put your TA server IP and token in each script. Every thing is done via API calls, so nothing additional.


## <ins>**Final Notes**:</ins>
I made these for personal use and have no issues with others taking and adapting to their needs, but I have no real intention of expanding these or doing major bug fixes. These are as-is.
