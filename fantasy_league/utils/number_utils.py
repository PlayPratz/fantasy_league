def rank_number_list(number_list: list, force_unique_ranks=False) -> list[int]:

    if force_unique_ranks:
        sorted_indexes = [
            i for i in sorted(enumerate(number_list), key=lambda x: x[1], reverse=True)
        ]
        ranks = [
            i[0] for i in sorted(enumerate(sorted_indexes, start=1), key=lambda x: x[1])
        ]

    else:
        rank_map = {}
        for rank, num in enumerate(sorted(number_list, reverse=True), start=1):
            if num not in rank_map:
                rank_map[num] = rank
        ranks = [rank_map[num] for num in number_list]

    return ranks
