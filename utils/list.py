def split_into_chunks(data: list, n: int):
    for i in range(0, len(data), n):
        yield data[i:i+n]

    # [data[i*n:(i+1)*n] for i in range((len(data) + n - 1) // n)]


if __name__ == "__main__":
    print(list(split_into_chunks([1, 1, 1, 2, 2, 2, 3], 3)))
    print(list(split_into_chunks([1, 1, 1, 1, 2, 2, 2, 2], 4)))
