# Copyright (c) 2026, Pratik Nerurkar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from fantasy_league.utils.number_utils import rank_number_list


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
            player_id = p.player
            fp = (
                self.fantasy_player_wo_id(player_id)
                .update(p)
                .update(self.single_player_points(player_id))
            )
            fp.pop("player")

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
                        self.fantasy_player_wo_id(r).update(player_points)
                    )
                fp["recent_points"] = fp["points"] - fp["previous_points"]
                fp["replacements"] = replacement_players

            players.append(fp)

        # Calculate ranks
        ranks = rank_number_list(list(p.points for p in players))
        previous_ranks = rank_number_list(list(p.previous_points for p in players))
        price_ranks = rank_number_list(list(p.price for p in players))
        for index, player in enumerate(players):
            player.rank = ranks[index]
            player.previous_rank = previous_ranks[index]
            player.price_rank = price_ranks[index]
            if player.rank <= self.best_of:
                player.counted = 1
            else:
                player.counted = 0

        return players

    def fantasy_player_wo_id(self, player_id) -> dict:
        fantasy_player = frappe.get_doc("Fantasy Player", player_id)
        fp = fantasy_player.as_dict(no_default_fields=True)
        fp.pop("player")
        return fp

    def single_player_points(self, player_id):
        player = frappe.get_doc(
            "Player in Fantasy Season",
            {"parent": self.name, "player": player_id},
        )
        player_dict = player.as_dict(no_default_fields=True, no_child_table_fields=True)
        player_dict.pop("player")
        return player_dict

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
                    "rank": t.rank,
                    "previous_rank": t.previous_rank,
                    "recent_rank_gain": t.recent_rank_gain,
                    "players": self.team_players(team_id),
                }
            )

        return teams

    def overview(self):
        return {
            "league_name": self.league_name,
            "season_year": self.season_year,
            "squad_size": self.squad_size,
            "overseas_limit": self.overseas_limit,
            "best_of": self.best_of,
            "commenced": self.commenced,
            "teams": self.all_teams(),
        }

    def before_save(self):

        # Update purses and points
        for t in self.teams:
            players = self.team_players(t.team)

            t.points = self.best_of_points(players)
            t.previous_points = self.best_of_previous_points(players)
            t.purse_spent = sum(p.price for p in players)

        team_ranks = rank_number_list(list(t.points for t in self.teams))
        team_previous_ranks = rank_number_list(
            list(t.previous_points for t in self.teams)
        )

        for index, t in enumerate(self.teams):
            t.rank = team_ranks[index]
            t.previous_rank = team_previous_ranks[index]
