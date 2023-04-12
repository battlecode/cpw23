import asyncio
from player import GameController

async def run_tourney(players):
    """
    Runs a complete round-robin tournament.
    \nArgs: players, a dictionary keyed on player ids
    \nReturns: a list of player ids in descending rank order
    """
    player_ids = generate_players(players)
    match_schedule = generate_schedule(player_ids)
    # player rankings: { player_id: { "played":, "won":, "lost":, } }
    rankings = { 
        player: { "played": 0, "won": 0, "lost": 0, "tied": 0, } 
        for player in player_ids 
    }
    # intitialize list of awaiting games
    waiting_list = []
    # make a list of our game runnables
    for match in match_schedule:
        waiting_list = asyncio.gather(*waiting_list, tourney_game(match, rankings))
    # run all games
    if waiting_list:
        await waiting_list
    # sort first on "won", then on "tied"
    rank_sort = sorted(rankings.items(), key=lambda x:x[1]["won"])
    rank_sort = sorted(rank_sort, lambda x:x[1]["tied"])
    return [ rank[0] for rank in rank_sort ]


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


async def tourney_game(competitors, rankings):
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
    # apply the results of the game to our rankings
    handle_outcome(match, rankings)


def handle_outcome(match, rankings):
    """
    Given a GameController that is completed, mutates a rankings 
    dict keyed on player_id to reflect the outcome. 
    """
    p1 = match.player1
    p2 = match.player2
    results = match.get_results()
    # if we have no results (game not over), throw error
    # games should always finish before the outcome is handled
    assert results, f"Game between {p1}, {p2} Not Finished!"
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