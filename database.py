import sqlite3
import re

# Table Structure

# Users Table
# Columns: Username, DiscordUserId

# Games Table
# Columns: GameId, UserId, Score, Won

# Messages
# Columns: LastParsedMessageId, ChannelId

def CreateTables(con):
    cur = con.cursor()

    cur.execute('''
    CREATE TABLE Users (
        username text, discord_user_id int,
        CONSTRAINT unique_users UNIQUE (discord_user_id)
    )

    ''')

    cur.execute('''
    CREATE TABLE Games (
        game_id int, discord_user_id int, score int, won bool,
        CONSTRAINT unique_games UNIQUE (game_id, discord_user_id)
    );
    ''')
    cur.execute('''
    CREATE TABLE LastMessage (
        last_parsed_message_id int, channel_id int,
        CONSTRAINT unique_channels UNIQUE (channel_id)
    )
    ''')

class WordleStats(object):
    def __init__(self, database, channel_id):
        self.database = database
        self.channel_id = channel_id

    def GetLastParsedMesasge(self):
        return self.database.GetLastParsedMesasge(self.channel_id)

    def _parseWordleGame(self, message_content):
        m = re.search(r'Wordle (\d+) (.)/6.*', message_content)
        if not m:
            return

        won = m.group(2) != 'X'
        score = int(m.group(2)) if won else 7 # TODO(ntr) idk what to do if its a loss?
        game_id = int(m.group(1))
        return (game_id, score, won)

    def ParseMessage(self, author_name, author_id, message_id, message_content):
        res = self._parseWordleGame(message_content)
        if res is None:
            self.database.UpdateLastParsedMessage(message_id, self.channel_id)
            return False

        game_id, score, won = res
        print('Recording Game {} from {} -- Score={}'.format(game_id, author_name, score))

        self.database.AddUserIfNecessary(author_name, author_id)
        self.database.RecordGame(author_id, game_id, score, won)
        self.database.UpdateLastParsedMessage(message_id, self.channel_id)
        return True

    def GetUserData(self, username):
        res = self.database.GetUserData(username)
        if res is None:
            return None

        raw_score, average_score, total_wins, total_games = res

        # Par is 4, so raw total score minus par times total number of games
        # will result in how much we're above or below par
        par = raw_score - (4 * total_games)
        total_losses = total_games - total_wins
        return par, average_score, total_losses

    def GetUserGameHistory(self, username, limit=10):
        res = self.database.GetUserGameHistory(username, limit)
        return res

    def GenerateLeaderboard(self):
        scores = self.database.GetAllUserScores()
        sorted_scores = sorted(scores, key=lambda x: x[1])
        return sorted_scores

class WordleDatabaseAccess(object):
    def __init__(self, database_name='wordle_stats.db'):
        self.connection = sqlite3.connect(database_name)

    def RecordGame(self, discord_user_id, game_id, score, didWin):
        cur = self.connection.cursor()
        cur.execute('''
                INSERT INTO Games
                VALUES(:game_id, :discord_user_id, :score, :won)
                ''', (game_id, discord_user_id, score, didWin))
        self.connection.commit()

    def AddUserIfNecessary(self, author_name, author_id):
        cur = self.connection.cursor()
        cur.execute('''
            INSERT OR IGNORE INTO Users VALUES(:author_name, :author_id)
            ''', (author_name, author_id))
        self.connection.commit()

    def GetLastParsedMesasge(self, channel_id):
        cur = self.connection.cursor()
        results = cur.execute('''
            SELECT last_parsed_message_id FROM LastMessage WHERE channel_id=:channel_id
            ''', {'channel_id': channel_id})
        rows = results.fetchall()
        if len(rows) == 0:
            return None
        return rows[0][0]

    def GetUserData(self, username):
        cur = self.connection.cursor()
        res = cur.execute('''
            SELECT SUM(Score), AVG(Score), COUNT(CASE WHEN Won THEN 1 END), Count(*) 
            FROM Games g 
            INNER JOIN Users u ON u.discord_user_id = g.discord_user_id 
            WHERE u.username=:username
            ''', {'username': username}).fetchall()
        if res[0][3] == 0:  # this is 0 total games, probably should figure out a better way to do this 
            return None
        return res[0]

    def GetUserGameHistory(self, username, limit=10):
        cur = self.connection.cursor()
        res = cur.execute('''
            SELECT game_id, score, won 
            FROM Games g 
            INNER JOIN Users u ON u.discord_user_id = g.discord_user_id 
            WHERE u.username=:username
            ORDER BY game_id DESC
            ''', {'username': username}).fetchall()
        return res[:limit] if limit is not None else res

    def GetAllUserScores(self):
        cur = self.connection.cursor()
        res = cur.execute('''
            SELECT u.username, SUM(Score) - 4 * COUNT(*) , COUNT(*)
            FROM Games g 
            INNER JOIN Users u ON u.discord_user_id = g.discord_user_id 
            GROUP BY u.username
            ''').fetchall()
        return res

    def UpdateLastParsedMessage(self, message_id, channel_id):
        last_message = self.GetLastParsedMesasge(channel_id)
        cur = self.connection.cursor()
        
        if last_message is None:
            cur.execute('''
                INSERT INTO LastMessage
                VALUES(:message_id, :channel_id)
                ''', (message_id, channel_id))
        else:
            cur.execute('''
                UPDATE LastMessage
                SET last_parsed_message_id=:message_id
                WHERE channel_id=:channel_id
                ''', (message_id, channel_id))
        self.connection.commit()

if __name__ == '__main__':
    import sys
    import os

    if len(sys.argv) != 2:
        print('Error running script...\nUsage: python3 {} <database_name>'.format(sys.argv[0]))
        exit(1)

    database_name = sys.argv[1]
    if os.path.exists(database_name):
        print('Found database file. Deleting...')
        os.remove(database_name)

    con = sqlite3.connect(database_name)
    CreateTables(con)
    print('Successfully created database file: {}'.format(database_name))