import json

class Config(object):
    def __init__(self, discord_token, guild_id, channel_id, database_name):
        self.discord_token = discord_token
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.database_name = database_name

    def __str__(self):
    	return 'DiscordToken={}; GuildId={}; ChannelId={}; DatabaseName={}'.format(self.discord_token,
    		self.guild_id,
    		self.channel_id,
    		self.database_name)

'''
JSON Structured like this
{
    'Dev': {
        'DiscordToken': ...
        'GuildId': ...
        'ChannelId': ...
        'DatabaseName': ...
    },
    'Prod': {
        'DiscordToken': ...
        'GuildId': ...
        'ChannelId': ...
        'DatabaseName': ...
    }
}
'''

def GetConfig(isProd=False):
    with open('config.json') as file:
        res = json.load(file)
        key = 'Prod' if isProd else 'Dev'
        config = res[key]
        return Config(config['DiscordToken'],
                      config['GuildId'],
                      config['ChannelId'],
                      config['DatabaseName'])