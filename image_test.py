import sqlite3
import matplotlib.pyplot as plt
from database import WordleStats, WordleDatabaseAccess

from matplotlib.ticker import MaxNLocator

ax = plt.figure().gca()
ax.xaxis.set_major_locator(MaxNLocator(integer=True))

if __name__ == '__main__':
	wda = WordleDatabaseAccess('prod_wordle_stats.db.bak')

	users = wda.GetAllUsers()
	latest_game_id = wda.GetLatestGame()
	games_to_include = 3
	starting_game_id = latest_game_id - games_to_include + 1
	starting_scores = wda.GetAllUserScoresAsOfGameId(starting_game_id)
	starting_scores_map = {tup[0]: tup[1] for tup in starting_scores}

	for user, discord_user_id in users:
		current_score = starting_scores_map[user]
		games = wda.GetUserGameHistorySinceGameId(user, starting_game_id)
		x = []
		y = []
		for game_id, raw_score, _ in reversed(games):
			score = raw_score - 4
			x.append(game_id)
			y.append(score + current_score)
			starting_scores_map[user] += score 
		plt.plot(x, y, marker='o', label=user)

	plt.xlabel('Game#')
	plt.ylabel('Par')
	plt.legend()
	plt.savefig('wordle_par.png')
	
	# plt.plot(x, y, marker='o')
	# plt.show()