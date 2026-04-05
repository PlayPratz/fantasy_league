def rank_number_list(number_list: list, use_order_if_equal=False) -> list[int]:
    rank_map = {}
    for rank, num in enumerate(sorted(number_list, reverse=True), start=1):
        if use_order_if_equal or num not in rank_map:
            rank_map[num] = rank
    ranks = [rank_map[points] for points in number_list]
    return ranks
