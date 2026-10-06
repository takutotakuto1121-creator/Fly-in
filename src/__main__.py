from src import Parser, MAPF

def main():
    parser = Parser()
    map = parser.parse("/Users/sugimototakuto/42cursus/Fly-in/maps/medium/03_priority_puzzle.txt")
    mapf = MAPF(map)
    paths, t = mapf.find_path()
    mapf.print_logs(paths, t)
    print(f"total turn: {t}")


if __name__ == "__main__":
    main()

