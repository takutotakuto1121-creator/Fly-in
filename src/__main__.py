from src import Visualizer
from src import Parser, MAPF
import sys


def main() -> None:
    if len(sys.argv) != 3:
        visualizer = Visualizer()
        visualizer.visualize()
    elif sys.argv[1] == "--log":
        parser = Parser()
        map = parser.parse(sys.argv[2])
        mapf = MAPF(map)
        paths, max_t = mapf.find_path()
        mapf.print_logs(paths, max_t)


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        print(f"[Error]{e}")
