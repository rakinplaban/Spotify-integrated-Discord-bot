from discord import app_commands, Interaction, Intents, Embed
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

load_dotenv()

# Discord bot token
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Spotify API credentials
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

SPOTIFY_SCOPE = (
    'user-read-playback-state '
    'user-read-currently-playing '
    'user-library-read '
    'user-read-private '
    'streaming'
)

# Set up Spotify authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=SPOTIFY_SCOPE,
    cache_path=".cache"
))

# token_info = sp_oauth.get_access_token()
# sp = spotipy.Spotify(auth=token_info['access_token'])


# Set up intents
intents = Intents.default()  # Default intents
intents.messages = True  # Explicitly enable message-related events (optional, depends on your use case)
intents.message_content = True  # Allows your bot to read message content
intents.members = True  # Allows your bot to access member-related events (optional, depends on your use case)


# Set up Discord bot
bot = commands.Bot(command_prefix='/',intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user.name}')

# @bot.command(name='current')
@bot.tree.command(name="current", description="Show what you are playing on Spotify!")
async def current(interaction):
    try:
        await interaction.response.defer(thinking=True) 
        current_track = sp.current_user_playing_track()
        if current_track and current_track['is_playing']:
            track_name = current_track['item']['name']
            artists = ", ".join([artist['name'] for artist in current_track['item']['artists']])
            album = current_track['item']['album']['name']
            album_cover_url = current_track['item']['album']['images'][0]['url']
            spotify_url = current_track['item']['external_urls']['spotify'] 

            embed = Embed(title="🎶 Now Playing", color=0x1DB954)
            embed.add_field(name="Track", value=track_name, inline=False)
            embed.add_field(name="Artist", value=artists, inline=True)
            embed.add_field(name="Album", value=album, inline=True)
            embed.set_thumbnail(url=album_cover_url)
            embed.add_field(name="Open in Spotify", value=spotify_url, inline=False)

            await interaction.followup.send(embed=embed)

            # await interaction.followup.send(f"🌸 Miku says: Now playing: '{track_name}' by {artists}")
        else:
            await interaction.followup.send("🌸 Miku says: No track is currently playing.")
    except Exception as e:
        await interaction.followup.send("🌸 Miku says: Oops, something went wrong.")
        print(e)


@bot.tree.command(name="play", description="Miku resumes your music.")
async def play(interaction: Interaction):
    try:
        sp.start_playback()
        await interaction.response.send_message("▶️ Miku resumed your music!", ephemeral=True)
    except:
        await interaction.response.send_message("⚠️ Couldn’t resume music. Are you playing anything?", ephemeral=True)



@bot.tree.command(name="pause", description="Miku pauses your Spotify music.")
async def pause(interaction: Interaction):
    try:
        sp.pause_playback()
        await interaction.response.send_message("⏸️ Miku paused your music.", ephemeral=True)
    except spotipy.exceptions.SpotifyException as e:
        await interaction.response.send_message("⚠️ Couldn't pause playback. Is Spotify running?", ephemeral=True)


def detect_mood(features):
    valence = features['valence']
    energy = features['energy']

    if valence > 0.6 and energy > 0.6:
        return "Happy 😄"
    elif valence > 0.6 and energy <= 0.5:
        return "Peaceful 🌸"
    elif valence < 0.4 and energy < 0.4:
        return "Sad 💧"
    elif valence < 0.4 and energy >= 0.6:
        return "Angsty 🔥"
    else:
        return "Neutral 🌀"


@bot.tree.command(name="mood", description="Miku tells you how you're feeling.")
async def mood(interaction: Interaction):
    try:
        current_track = sp.current_user_playing_track()
        if current_track and current_track['is_playing']:
            track_id = current_track['item']['id']
            print("Track ID:", track_id)  # ← LOG FIRST
            print("Getting audio features...")

            features = sp.audio_features([track_id])[0]
            print("Got features:", features)

            if features is None:
                await interaction.response.send_message("🌸 Miku couldn't read this track's mood.", ephemeral=True)
                return

            mood = detect_mood(features)
            await interaction.response.send_message(
                f"🌸 Miku says: You're feeling **{mood}**.\n🎵 *{current_track['item']['name']}* by *{current_track['item']['artists'][0]['name']}*",
                ephemeral=True
            )
        else:
            await interaction.response.send_message("🌸 Miku says: No track is currently playing.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message("🌸 Miku says: Oops, something went wrong.", ephemeral=True)
        print("Mood command error:", e)




if __name__=='__main__':
    print("Authenticated user:", sp.current_user()['display_name'])
    bot.run(DISCORD_TOKEN)
    


