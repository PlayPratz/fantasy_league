# Copyright (c) 2026, Pratik Nerurkar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FantasySeason(Document):

    def team_players(self, team_id) -> dict:
        players_sign = frappe.get_all(
            "Signing in Fantasy Season",
            filters={"parent": self.name, "team": team_id},
            fields=["player", "slot_number", "price"],
        )

        players = []

        # Get player_name and fantasy_player_id
        for p in players_sign:
            fantasy_player = frappe.get_doc("Fantasy Player", p.player)
            player_id = fantasy_player.name

            fp = fantasy_player.as_dict(no_default_fields=True).update(p)
            fp.pop("player")

            replacements = self.all_replacements_for([player_id])
            if len(replacements) > 1:
                fp["points"] = 0
                fp["recent_points"] = 0
                replacement_players = []
                for r in replacements:
                    player_points = self.single_player_points(r)
                    fp["points"] += player_points["points"]
                    fp["recent_points"] += player_points["recent_points"]
                    replacement_players.append(
                        {
                            "player_name": frappe.get_value(
                                "Fantasy Player", r, "player_name"
                            ),
                            **player_points,
                        }
                    )
                fp["replacements"] = replacement_players
            else:
                player_points = self.single_player_points(player_id)
                fp.update(player_points)

            players.append(fp)
        players.sort(key=lambda p: p.slot_number)
        return players

    def single_player_points(self, player_id):
        return frappe.get_value(
            "Player in Fantasy Season",
            {"parent": self.name, "player": player_id},
            ["points", "recent_points"],
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

    def best_of_points(self, point_list):
        best_points = sorted(point_list, reverse=True)[: self.best_of]
        return sum(best_points)

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
                    "recent_points": t.recent_points,
                    "highest_points": t.highest_points,
                    "highest_spend": t.highest_spend,
                    "players": self.team_players(team_id),
                }
            )

        return teams

    def before_save(self):
        for t in self.teams:
            players = self.team_players(t.team)
            only_points = [p["points"] for p in players]
            t.points = self.best_of_points(only_points)
            t.highest_points = max(only_points)
            t.highest_spend = max(p["price"] for p in players)

            team_previous_points = self.best_of_points(
                p["points"] - p["recent_points"] for p in players
            )
            t.recent_points = t.points - team_previous_points
            print("Updated for ", t.team)

        # # Update purses and points
        # purse_spent_map = {}

        # player_to_team_map = {}

        # team_points_map = {}
        # team_recent_points_map = {}

        # # team_rank_map = {}
        # # team_previous_rank_map = {}

        # for t in self.teams:
        #     purse_spent_map[t.team] = 0
        #     team_points_map[t.team] = 0
        #     team_recent_points_map[t.team] = 0

        # # Accumulate purse_spent
        # for s in self.player_signings:
        #     purse_spent_map[s.team] += s.price
        #     player_to_team_map[s.player] = s.team

        # # Accumulate points
        # for p in self.player_pool:
        #     if p.player in player_to_team_map:
        #         team = player_to_team_map[p.player]
        #         team_points_map[team] += p.points
        #         team_recent_points_map[team] += p.recent_points

        # # Calculate ranks

        # # Update values
        # for t in self.teams:
        #     t.purse_spent = purse_spent_map[t.team]
        #     t.points = team_points_map[t.team]
        #     t.recent_points = 0  # Todo
