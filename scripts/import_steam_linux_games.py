# pylint: disable=missing-docstring
import logging
import requests
from games.models import Game
from games.util.steam import get_store_info, create_steam_installer
from common.util import slugify

LOGGER = logging.getLogger(__name__)


def run():
    response = requests.get(
        "https://raw.githubusercontent.com/SteamDatabase/SteamLinux/master/GAMES.json"
    )
    linux_games = response.json()
    for game_id in linux_games:
        if linux_games[game_id] is not True:
            LOGGER.debug(
                "Game %s likely has problems, skipping. "
                "This game should be added manually if appropriate.",
                game_id
            )
            continue
        if Game.objects.filter(steamid=game_id).count():
            # LOGGER.debug("Game %s is already in Lutris", game_id)
            continue
        store_info = get_store_info(game_id)
        if not store_info:
            LOGGER.warning("No store info for game %s", game_id)
            continue

        if store_info["type"] != "game":
            LOGGER.warning("%s: %s is not a game (type: %s)", game_id, store_info["name"], store_info["type"])
            continue
        slug = slugify(store_info["name"])
        if Game.objects.filter(slug=slug).count():
            LOGGER.warning("Game %s already in Lutris but does not have a Steam ID", game_id)
            continue

        game = Game.objects.create(
            name=store_info["name"],
            slug=slug,
            steamid=game_id,
            description=store_info["about_the_game"],
            website=store_info["website"] or "",
            is_public=True,
        )
        game.set_logo_from_steam()
        game.save()
        LOGGER.debug("%s created", game)
        if store_info["platforms"]["linux"]:
            LOGGER.info("Creating installer for %s", game)
            create_steam_installer(game)
