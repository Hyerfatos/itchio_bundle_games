#!/usr/bin/env python3

"""
Download the name of all games in the bundle.
Download their info and scrore from opencritic if they exist there.
Sort by score.
"""

import json
import urllib.request
import urllib.parse
from typing import List

from bs4 import BeautifulSoup
from typing_extensions import TypedDict


Game = TypedDict(
    "Game",
    {
        "name": str,
        "itch": str,
        "opencritic": str,
        "steam": str,
        "score": int,
        "correct": float,
        "description": str,
        "genres": List[str],
    },
)


def get_game_list() -> List[Game]:
    """
    Get the game list from the bundle.
    """
    #  bundle_url = "https://itch.io/b/520/bundle-for-racial-justice-and-equality"
    # As I need to scroll to the bottom of the page I just used javascript to do
    # that and saved the resulted html into a file.

    with open("itchio_520.html", "r",) as inf:
        soup = BeautifulSoup(inf, "html.parser")

    games: List[Game] = []

    games_soup = soup.find_all("div", class_="index_game_cell_widget game_cell")

    for game in games_soup:
        info = game.find("div", class_="label").a.attrs
        games.append(
            {
                "name": info["title"],
                "itch": info["href"],
                "opencritic": "",
                "steam": "",
                "score": -1,
                "correct": -1,
                "description": "",
                "genres": [],
            }
        )

    return games


def get_opencritic_info(games: List[Game]) -> List[Game]:
    """
    Get information from opencritic regarding the game.
    """
    url_api_search = "https://api.opencritic.com/api/game/search?"
    url_api_game = "https://api.opencritic.com/api/game/{}"
    url_opencritic = "https://www.opencritic.com/game/{}/{}"
    url_steam = "https://store.steampowered.com/app/{}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0"
    }

    for game in games:
        print("Getting info for: {}".format(game["name"]))
        # Search for the game, Assume the first respond is the correct one
        url1 = url_api_search + urllib.parse.urlencode({"criteria": game["name"]})
        request1 = urllib.request.Request(url1, None, headers)
        respond1 = json.loads(
            urllib.request.urlopen(request1).read().decode("utf-8")
        )[0]

        # From 0.2 to 0.3 some games where correct some not
        if respond1["dist"] > 0.3:
            continue

        # Get game info
        url2 = url_api_game.format(respond1["id"])
        request2 = urllib.request.Request(url2, None, headers)
        respond2 = json.loads(
            urllib.request.urlopen(request2).read().decode("utf-8")
        )

        game["correct"] = respond1["dist"]
        game["score"] = respond2.get("medianScore", -1)
        game["opencritic"] = url_opencritic.format(respond1["id"], respond1["name"])
        game["steam"] = url_steam.format(respond2.get("steamId", ""))
        game["description"] = respond2.get("description", "")
        game["genres"] = [val["name"] for val in respond2.get("Genres", [])]

    return games


def sort_by_score(games: List[Game]) -> List[Game]:
    """
    Sort the games by score.
    """
    games = sorted(games, key=lambda k: k['score'], reverse=True)
    return games


if __name__ == "__main__":
    print("Getting the game list")
    my_games = get_game_list()

    with open("all_games.json", "w") as outf:
        json.dump(my_games, outf, indent=2)

    print("Getting info from opencritic")
    my_games = get_opencritic_info(my_games)

    print("Sorting games")
    my_games = sort_by_score(my_games)

    with open("games.json", "w") as outf:
        json.dump(my_games, outf, indent=2)
