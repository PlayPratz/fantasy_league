def rank_number_list(number_list: list, force_unique_ranks=False) -> list[int]:

    if force_unique_ranks:
        sorted_number_list = sorted(number_list, reverse=True)
        ranks = [sorted_number_list.index(num) + 1 for num in number_list]

    else:
        rank_map = {}
        for rank, num in enumerate(sorted(number_list, reverse=True), start=1):
            if num not in rank_map:
                rank_map[num] = rank
        ranks = [rank_map[num] for num in number_list]

    return ranks
