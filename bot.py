import nextcord
from nextcord.ext import tasks
import sqlite3

from database import WordleStats, WordleDatabaseAccess

kUserStatsMessage = '''
Player {}
Par: {}
Average Score: {}
Total Losses: {}
'''

kHistoryLine = 'Wordle {}: {}/6'

class WordleStatBot(nextcord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.channel_id = kwargs['channel_id']
        database_name = kwargs['database']

        self.database = WordleStats(WordleDatabaseAccess(database_name), self.channel_id)
        
        self.my_background_task.start()

    @tasks.loop(seconds=15)
    async def my_background_task(self):
        await self.poll_new_messages()


    @my_background_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready() # wait until the bot logs in

    async def get_all_messages_since_message(self, last_message):
        channel = self.get_channel(self.channel_id) 
        messages = []
        limit = 200

        res = await channel.history(limit=limit, oldest_first=True, after=last_message).flatten()
        messages.extend(res)

        while len(res) != 0:
            res = await channel.history(limit=limit, oldest_first=True, after=messages[-1]).flatten()
            messages.extend(res)

        return messages

    async def poll_new_messages(self):
        channel = self.get_channel(self.channel_id) 

        last_message_id = self.database.GetLastParsedMesasge()
        last_message = channel.get_partial_message(last_message_id) if last_message_id is not None else None

        # TODO(ntr) if this is empty, we should log saying we caught up 
        messages = await self.get_all_messages_since_message(last_message)
        for message in messages:
            try:
                wasGame = self.database.ParseMessage(message.author.name, message.author.id, message.id, message.content)
                if wasGame:
                    await message.add_reaction('🟩') # Green Square
            except Exception as e:
                print('Exception thrown parsing message', e)

    def _addCodeBlocks(self, string):
        return '```' + string + '```'

    async def user_stats(self, interaction, member):
        res = self.database.GetUserData(member.name)
        if res is None:
            await interaction.response.send_message("{} has not played any loaded games".format(member.name))
        else:
            par, average_score, total_losses = res
            message = kUserStatsMessage.format(member.name, par, average_score, total_losses)
            await interaction.response.send_message(self._addCodeBlocks(message))

    async def user_history(self, interaction, member, limit):
        limit = None if limit == 0 else limit
        res = self.database.GetUserGameHistory(member.name, limit)
        if len(res) == 0:
            await interaction.response.send_message("{} has not played any loaded games".format(member.name))
        else:
            lines = []
            if limit is None:
                lines.append('All games for {}'.format(member.name))
            else:
                lines.append('Previous {} game{} for {}'.format(limit, '' if limit == 1 else 's', member.name))

            lines.extend(kHistoryLine.format(*i) for i in res)
            message = '\n'.join(lines)
            await interaction.response.send_message(self._addCodeBlocks(message))

    async def leaderboard(self, interaction):
        res = self.database.GenerateLeaderboard()

        table_data = []
        for ranking, user_data in enumerate(res):
            table_data.append((ranking+1,) + user_data)

        from tabulate import tabulate
        table = tabulate(table_data, headers=["Rank", "User", "Par", "Total Games"])

        await interaction.response.send_message('```' + table + '```')
