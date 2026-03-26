import frappe


@frappe.whitelist(methods=["POST"])
def add_players(players):
    for p in players:
        add_fantasy_player_inner(p["Name"], p["Id"])

    return f"Created {len(players)} records"


def add_fantasy_player_inner(player_name, fantasy_id):
    player_id = frappe.get_value("Player", {"player_name": player_name}, ["name"])
    if not player_id:
        new_player = frappe.get_doc(
            {
                "doctype": "Player",
                "player_name": player_name,
                "short_name": player_name.split()[0],
            }
        )
        new_player.insert()
        player_id = new_player.name
    new_fantasy_player = frappe.get_doc(
        {
            "doctype": "Fantasy Player",
            "player": player_id,
            "player_name": player_name,
            "fantasy_player_id": fantasy_id,
        }
    )
    new_fantasy_player.insert()


@frappe.whitelist(methods=["POST"])
def create_season_pool(season, players):
    for p in players:
        pname = p["Name"]
        fantasy_player_id = frappe.get_value(
            "Fantasy Player", {"fantasy_player_id": p["Id"]}, ["name"]
        )

        if not fantasy_player_id:
            add_fantasy_player_inner(p["Name"], p["Id"])
            fantasy_player_id = frappe.get_value(
                "Fantasy Player", {"player_name": pname}, ["name"]
            )

        player_in_season = frappe.get_doc(
            {
                "doctype": "Player in Fantasy Season",
                "parent": season,
                "parenttype": "Fantasy Season",
                "parentfield": "player_pool",
                "player": fantasy_player_id,
                "ipl_team": p["TeamShortName"],
                "overseas": int(p["IS_FP"]),
            }
        )
        player_in_season.insert()
    return f"Added {len(players)} players to Season {season}"


@frappe.whitelist(methods=["POST"])
def create_auction_signings(season, signings):
    for s in signings:
        player_id = frappe.get_value(
            "Fantasy Player", {"fantasy_player_id": s["id"]}, "name"
        )
        signing = frappe.get_doc(
            {
                "doctype": "Signing in Fantasy Season",
                "parent": season,
                "parenttype": "Fantasy Season",
                "parentfield": "player_signings",
                "type": "Auction",
                "player": player_id,
                "team": s["team_id"],
                "price": s["price"],
            }
        )

        signing.insert()

    return f"Created {len(signings)} auction signings"


@frappe.whitelist(methods=["PUT"])
def update_points(season, players):
    fantasy_season = frappe.get_doc("Fantasy Season", season)

    player_to_point_map = {}
    player_to_recent_point_map = {}

    for p in players:
        player_to_point_map[p["Id"]] = p["OverallPoints"]
        player_to_recent_point_map[p["Id"]] = p["GamedayPoints"]

    for p in fantasy_season.player_pool:
        fantasy_player_id = frappe.get_value(
            "Fantasy Player", p.player, "fantasy_player_id"
        )
        p.points = player_to_point_map[fantasy_player_id]
        p.previous_points = p.points - player_to_recent_point_map[fantasy_player_id]

    fantasy_season.save()
    return f"Updated points for {len(players)} players"


@frappe.whitelist(allow_guest=True, methods=["GET"])
def fantasy_season(season):
    season = frappe.get_doc("Fantasy Season", season)
    return season.overview()


@frappe.whitelist(allow_guest=True, methods=["GET"])
def fantasy_season_list():
    return frappe.get_all(
        "Fantasy Season",
        [
            "name",
            "league_name",
            "season_year",
            "squad_size",
            "overseas_limit",
            "best_of",
            "commenced",
        ],
        order_by="season_year desc",
    )


@frappe.whitelist(methods=["PUT"])
def usethis():
    fantasy_seasons = frappe.get_list(
        "Fantasy Season",
        filters={"auto_update_points": 1},
        fields={"name", "update_points_url"},
    )
    for fs in fantasy_seasons:
        players = frappe.integrations.utils.make_get_request(fs.update_points_url)[
            "Data"
        ]["Value"]["Players"]
        return update_points(fs.name, players)


@frappe.whitelist(methods=["GET"])
def test():
    return frappe.get_all("Team in Fantasy Season", fields="*")
