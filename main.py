from nextcord import Member, Interaction, SlashOption
import argparse

from bot import WordleStatBot
from config import GetConfig

parser = argparse.ArgumentParser(description='Run the Wordle Stats bot')
parser.add_argument('--prod', help='use prod configurations', action='store_true')
args = parser.parse_args()

print('Starting Wordle Stat Bot... Environment={}'.format('Prod' if args.prod else 'Dev'))

config = GetConfig(args.prod)
client = WordleStatBot(channel_id=config.channel_id, database=config.database_name)

@client.slash_command(guild_ids=[config.guild_id])
async def stats(
    interaction: Interaction,
    member: Member = SlashOption(name="user", description="User to request stats for", required=True)
    ):
    await interaction.client.user_stats(interaction, member)


@client.slash_command(guild_ids=[config.guild_id])
async def leaderboard(interaction: Interaction):
    await interaction.client.leaderboard(interaction)

client.run(config.discord_token)
