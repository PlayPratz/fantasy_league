# Copyright (c) 2026, Pratik Nerurkar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FantasySeason(Document):

    def team_players(self, team_id) -> dict:
        players_sign = frappe.get_all(
            "Signing in Fantasy Season",
            filters={"parent": self.name, "team": team_id},
            fields=["player", "slot_number", "type", "price"],
            order_by="slot_number asc",
        )

        players = []
        # Get player_name and fantasy_player_id
        for p in players_sign:
            fantasy_player = frappe.get_doc("Fantasy Player", p.player)
            player_id = fantasy_player.name

            fp = fantasy_player.as_dict(no_default_fields=True).update(p)
            fp.pop("player")

            player_points = self.single_player_points(player_id)
            fp.update(player_points)

            # Check for replacements
            replacements = self.all_replacements_for([player_id])
            if len(replacements) > 1:
                fp["points"] = 0
                fp["previous_points"] = 0
                replacement_players = []
                for r in replacements:
                    player_points = self.single_player_points(r)
                    fp["points"] += player_points["points"]
                    fp["previous_points"] += player_points["previous_points"]
                    replacement_players.append(
                        {
                            "player_name": frappe.get_value(
                                "Fantasy Player", r, "player_name"
                            ),
                            **player_points,
                        }
                    )
                fp["recent_points"] = fp["points"] - fp["previous_points"]
                fp["replacements"] = replacement_players

            players.append(fp)

        # Calculate ranks
        ranks = self.rank_points_list(list(p.points for p in players))
        previous_ranks = self.rank_points_list(list(p.previous_points for p in players))
        for index, player in enumerate(players):
            player.rank = ranks[index]
            player.previous_rank = previous_ranks[index]

        return players

        # for rank, player in enumerate(
        #     sorted(
        #         slot_to_player_map.items(),
        #         key=lambda item: item[1].points,
        #         reverse=True,
        #     ),
        #     start=1,
        # ):
        #     fp = player[1]
        #     fp.rank = rank

        # Calculate previous_ranks
        # for rank, player in enumerate(
        #     sorted(
        #         slot_to_player_map.items(),
        #         key=lambda item: item[1].previous_points,
        #         reverse=True,
        #     ),
        #     start=1,
        # ):
        #     fp = player[1]
        #     fp.previous_rank = rank

        # return list(slot_to_player_map.values())

    def rank_points_list(self, points_list: list) -> list[int]:
        rank_map = {}
        for rank, points in enumerate(sorted(points_list, reverse=True), start=1):
            rank_map[points] = rank
        ranks = [rank_map[points] for points in points_list]
        return ranks

    def single_player_points(self, player_id):
        return frappe.get_value(
            "Player in Fantasy Season",
            {"parent": self.name, "player": player_id},
            ["overseas", "points", "previous_points", "recent_points"],
            as_dict=True,
        )

    def all_replacements_for(self, player_ids: list[str]) -> list[str]:
        replacement_id = frappe.get_value(
            "Replacement in Fantasy Season",
            {"parent": self.name, "old_player": player_ids[-1]},
            ["new_player"],
        )
        if replacement_id:
            player_ids.append(replacement_id)
            return self.all_replacements_for(player_ids)
        else:
            return player_ids

    def best_of_points(self, players):
        return sum(p.points for p in players if p.rank <= self.best_of)

    def best_of_previous_points(self, players):
        return sum(
            p.previous_points for p in players if p.previous_rank <= self.best_of
        )

    def all_teams(self):
        teams = []
        for t in self.teams:
            team_id = t.team
            teams.append(
                {
                    "team": team_id,
                    "team_owner": frappe.get_value(
                        "Fantasy Team", team_id, "team_owner"
                    ),
                    "points": t.points,
                    "previous_points": t.previous_points,
                    "recent_points": t.recent_points,
                    "highest_points": t.highest_points,
                    "highest_spend": t.highest_spend,
                    "players": self.team_players(team_id),
                }
            )

        return teams

    def before_save(self):

        # Update purses and points

        for t in self.teams:
            players = self.team_players(t.team)

            t.points = self.best_of_points(players)
            t.previous_points = self.best_of_previous_points(players)
            t.purse_spent = sum(p.price for p in players)

            print("Updated for ", t.team)

        team_ranks = self.rank_points_list(list(t.points for t in self.teams))
        team_previous_ranks = self.rank_points_list(
            list(t.previous_points for t in self.teams)
        )

        for index, t in enumerate(self.teams):
            t.rank = team_ranks[index]
            t.previous_rank = team_previous_ranks[index]
