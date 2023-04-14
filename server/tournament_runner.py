import asyncio
from player import GameController

async def run_tourney(players):
    """
    Runs a complete round-robin tournament.
    \nArgs: players, a dictionary keyed on player ids
    \nReturns: a list of player ids in descending rank order
    """
    match_schedule = generate_schedule(players)
    # player rankings: { player_id: { "played":, "won":, "lost":, "tied":, } }
    rankings = { 
        player: { "played": 0, "won": 0, "lost": 0, "tied": 0, } 
        for player in players 
    }
    # intitialize list of awaiting games
    waiting_list = []
    # make a list of our game runnables
    for match in match_schedule:
        waiting_list = asyncio.gather(*waiting_list, tourney_game(match))
    # run all games
    if waiting_list:
        # collect results
        results = await waiting_list
        # apply results to rankings
        for result in results:
            handle_outcome(result, rankings)
    # return our list of player_ids, sorted by rank
    return rank_sort(rankings)


def generate_schedule(players):
    """
    Generates a match schedule for each player to play against every
    other n-1 players.
    \nArgs: players, a dictionary keyed on player ids
    \nReturns: a set of tuples (player1_id, player2_id), every 2-element
    permutation of player ids.
    """
    player_ids = generate_players(players)
    match_schedule = set()
    for player_idx, player_id in enumerate(player_ids):
        opponents = player_ids[:player_idx] + player_ids[player_idx+1:]
        for opp_id in opponents:
            match_schedule.add(tuple(sorted((player_id, opp_id))))
    return match_schedule


def generate_players(players):
    """
    Given a player dict, return a list of all player ids.
    """
    return [ player for player in players ]


async def tourney_game(competitors):
    """
    Given a tuple of competitors and a rankings dict, run a game between them.
    Mutate rankings with each players' match results.
    The two players should not currently be in a game.
    """
    # get our two competitors
    p1, p2 = competitors
    # run our game
    match = GameController(p1, p2)
    await match.play_game()
    # return match object
    return match


def handle_outcome(match, rankings):
    """
    Given a GameController that is completed, mutates a rankings 
    dict keyed on player_id to reflect the outcome. 
    """
    p1 = match.player1
    p2 = match.player2
    results = match.get_results()
    # handle win/loss outcome
    winner = results[0]
    rankings[p1]["played"] += 1
    rankings[p2]["played"] += 1
    # if winner = None, we have a tie
    if not winner:
        rankings[p1]["tied"] += 1
        rankings[p2]["tied"] += 1
    else:
        # create holder for loser
        loser = p1 if p1 != winner else p2
        # apply results
        rankings[winner]["won"] += 1
        rankings[loser]["lost"] += 1


def rank_sort(rankings):
    """
    Given a rankings dict and match list, return a list of player ids in
    rank order based on the following criteria:
     - Win = 3 pts.
     - Tie = 1 pt.
     - Loss = 0 pts.\n
    Divided by games played, creating a pts/game ranking.\n
    pts/game ties are broken by # of wins, then head to head result,
    then a coin flip.
    """
    new_ranks = { player_id: {"win_pct": 0, "won": rankings[player_id]["won"],} for player_id in rankings }
    for player_id, results in rankings.items():
        new_ranks[player_id]["win_pct"] = int(
            ((3*results["won"]) + 
            (1*results["tied"])) /
            results["played"] * 10000
        ) / 10000
    sorted_rank = sorted(new_ranks.items(), key=lambda x: (x[1]["win_pct"], x[1]["won"]), reverse=True)
    return [ rank[0] for rank in sorted_rank ]
