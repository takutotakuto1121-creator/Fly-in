# Fly-in
## Description
*Fly-in* is a solo project at Milestone 3 of the 42cursus. The goal is to launch multiple drones from the start at the same time and find routes that bring all of them to the goal efficiently. It teaches multi-agent path finding, maximum flow problems, and more.
### Map format
The map is given in the following format.

```
nb_drones: 5
start_hub: start 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: node 5 5[zone=restricted color=red]
connection: start-node [max_link_capacity=2]
connection: node-goal
```
The rules are as follows.
1. The first line must be `nb_drones`, which specifies the number of drones.
2. Hubs (nodes) are specified with `start_hub`, `end_hub`, and `hub: name x y [metadata]`.
3. The hub metadata follows these rules.  
`zone=type` (default: `normal`): if the type is `normal`, it is a standard hub and moving into it takes 1 turn. If `blocked`, entering the zone is forbidden. If `restricted`, moving into it takes 2 turns. If `priority`, moving into it takes 1 turn and it should be preferred as a route.  
`color=value` (default: none): the color of the hub.  
`max_drones=number` (default: 1): the maximum number of drones that can stay in the hub at the same time.
4. `connection: name1-name2 [metadata]` represents a link between the hubs name1 and name2.
5. The connection metadata follows this rule.  
`max_link_capacity=number` (default: 1): the maximum number of drones that can traverse the edge at the same time.

## Instructions
Run the project with the following steps.
```bash
# Clone the repository
git clone https://github.com/takutotakuto1121-creator/Fly-in.git Fly-in

# Move into the repository
cd Fly-in

# Run
make run
```

A window like the following will open.

![image](assets/screen_1.png)

Select a map with the Enter key.
Once you have made your selection, the map is displayed as below, and you can move time forward and backward with the arrow keys to watch the drones' behavior.

![image](assets/screen_2.png)

If you only want the log printed to the terminal, run the following command.
If ARG is not specified, `maps/hard/03_ultimate_challenge.txt` is used by default.
```bash
make log ARG=[path to map]
```

## Algorithm
### Parsing
The text file describing the map is parsed.
Parsing is validated with pydantic, but since the focus of this project is path finding and visualization, I omit the details here. The code is easy to follow.

### Time-expanded Network Flow
This is implemented by introducing the concept of time and space into maximum flow. The maximum flow problem is: given a graph, find the maximum amount of water that can be sent through it. I leave the explanation of it to [this site](). [DFS]() is used for path finding. Let me explain with a concrete example. Suppose the following map is given (the map from maps/medium/03_priority_puzzle.txt).
```
# Medium Level 3: Priority zones create optimal path challenges
nb_drones: 5

start_hub: start 0 0 [color=green]
hub: slow_path1 1 -1 [zone=restricted color=red]
hub: slow_path2 2 -1 [color=red]
hub: fast_junction 1 0 [zone=priority color=blue max_drones=2]
hub: fast_path 2 0 [zone=priority color=blue]
hub: merge_point 3 0 [color=yellow max_drones=3]
end_hub: goal 4 0 [color=green]

connection: start-slow_path1
connection: start-fast_junction
connection: slow_path1-slow_path2
connection: slow_path2-merge_point
connection: fast_junction-fast_path
connection: fast_path-merge_point
connection: merge_point-goal [max_link_capacity=2]

```
Visualizing this graph gives the picture below. Only the slightly thicker edge (merge_point -> goal) allows two drones to pass at the same time. Moving from node to node through a normal edge takes only 1 turn, but moving into the restricted nodes slow_path1 and slow_path2 takes 2 turns. There are none in this example, but if a blocked node exists, it is not generated at this stage and is removed from the graph entirely.

![image](assets/graph_1.png)

First, handling the number of drones that can exist in each node at the same time directly in the program would be very complicated, so each node is split into an in node and an out node. The edge connecting in and out is given a sufficiently large capacity. This removes one condition we have to consider. The graph looks like this.

![image](assets/graph_2.png)

Let's remove one more condition. When moving into the restricted nodes slow_path1 and slow_path2, a dummy node is inserted in between, and the number of drones that can move through the dummy node is made equal to the number of drones that can exist in the node at the same time. Here it is 1 for both slow_path1 and slow_path2, so we set it to 1. Now all nodes can be treated equally, and the only thing to consider is the capacity of the edges. The conditions are now much simpler. The graph looks like this.

![image](assets/graph_3.png)

On this graph, we build an algorithm that sends multiple drones from start_in and gets all of them to goal_out in the fewest turns.
First, consider a graph for each time t (an integer greater than or equal to 0). Each time t increases by one, one turn passes.
In the initial state there are no edges, only nodes.
At t=0, only the edge start_in -> start_out is created.
At t=1, only the in -> out edge of each node (excluding dummy nodes) is created.
The graph looks like this.
Let's also run DFS at t=0. Of course, there is no path that reaches the goal.

![image](assets/graph_4.png)

At this point, the graphs for t=0 and t=1 live in different spacetimes. Each graph is independent and they do not intersect.
Regarding path finding: with a single agent (a single drone here), the shortest path can be found with plain BFS or Dijkstra. But this is multi-agent (multiple drones), so ordinary path finding makes the problem very hard to solve.
To solve this, I implemented it by connecting the different spacetimes. The graph below is 2D, but it may help to imagine t=0 and t=1 stacked vertically in 3D.
Going from t=0 to t=1 means one turn passes. So movement between nodes is made possible at the moment of going from t=0 to t=1.
In each turn, a drone can either wait or move.
For waiting, connect start_out(t=0) (hereafter written as start_out in t=0) to start_in(t=1) with an edge. Likewise, create an in(t=0) -> out(t=1) edge for each node. This is equivalent to a drone staying at the node without moving as the turn passes.
For moving, first consider edges between normal nodes. For example, look at fast_junction -> fast_path. Create the edges fast_junction_out(t=0) -> fast_path_in(t=1) and fast_path_out(t=0) -> fast_junction_in(t=1). This enables movement in both directions in one turn.
Next, consider the case where the destination is a restricted node. For example, look at start -> slow_path1. Create the edges start_out(t=0) -> dummy1_in(t=1), dummy1_in(t=1) -> dummy1_out(t=1), and slow_path1_out(t=0) -> start_in(t=1). The key point is that a dummy node is inserted in between. For why this delays the drone by one turn, see the explanation of the state up to t=2 below.
Finally, consider the case where the source is a restricted node. For example, look at slow_path2 -> merge_point. Create the edges slow_path2_out(t=0) -> merge_point_in(t=1), merge_point_out(t=0) -> dummy3_in(t=1), and dummy3_in(t=1) -> dummy3_out(t=1). Again, the key point is that a dummy node is inserted in between.
In this space connecting t=0 and t=1, run DFS with start_in(t=0) as the start and goal_out(t=1) as the goal. No path is found yet.

![image](assets/graph_5.png)

From here on, we just repeat the above operations.
The one difference from then on is in the edge creation for restricted nodes: in this example, edges connecting the dummy nodes and the restricted nodes, such as dummy1_out(t=1) -> slow_path1_in(t=2), are added. Only at this point does moving into a restricted node become possible. This is how moving into a restricted node takes 2 turns.
Run DFS again in the space connecting t=0, 1, and 2. The start is start_in(t=0) and the goal is goal_out(t=2). No path is found yet.

![image](assets/graph_6.png)

By repeating this operation, the space is expanded little by little, movement per turn is realized, and paths are searched. At time t, the start is start_in(t=0) and the goal is goal_out(t=t).

## Multi-agent path finding with DFS
If we repeat this, DFS will eventually find a path. But so far there is only one agent (drone). Let's now think about how to find paths for multiple agents (two or more).
Let's reconsider the map. By splitting nodes into in and out at the very beginning and inserting dummy nodes when moving into restricted nodes, the data we have to consider has become three things: nodes, edges, and the maximum number of drones that can pass each edge at a time.
Let's focus on the maximum number of drones that can pass each edge at a time. In `mapf.py`, the Edge class is defined as follows.
```python
class Edge:
    def __init__(self, to_node: tuple[str, str, int], cap: int, is_forward: bool):
        self.to: tuple[str, str, int] = to_node
        self.cap: int = cap
        self.rev: Optional[Edge] = None
        self.is_forward: bool = is_forward
```
Each edge holds the following: `to` is the node the edge points to, `cap` is the maximum number of drones that can pass the edge at a time, `rev` is the edge in the opposite direction (the cancel route), and `is_forward` indicates whether this edge is a forward edge (i.e., not a cancel route).
`cap` is the important part. Consider the case where, at a turn transition (a change of t), a drone moves instead of waiting during the DFS. It uses edges to move. First, run DFS once and find the shortest path; then decrease `cap` of each edge used by 1 and increase `cap` of its `rev` by 1. Then run DFS again in that state, and repeat. Repeat this until no more paths can be found; finish once the number of paths found is greater than or equal to the number of drones.
Increasing the `cap` of `rev` by 1 means that, once a drone has found a path from start to goal, the exact reverse of that route is added using edges.
Going back to the starting point, the policy was to solve the problem by applying maximum flow. In maximum flow, we send as much water as possible. Now consider the following graph.

![image](assets/graph_7.png)

If we send as much water as possible from start to goal in this graph, the water collides at the node1 - node2 edge and cannot flow. So the routes the water takes should be the two routes start->node1->goal and start->node2->goal. However, suppose the first search finds the route start->node1->node2->goal. Then the caps of start->node1, node1->node2, and node2->goal change from 1 to 0, and if we simply search again, no path is found. This is because water collisions are not taken into account.

So we create the reverse route (cancel route) of the route we just found, and then search again. When we add the cancel route goal->node2->node1->start and search, we find the route start->node2->node1->goal.
With cancel routes created like this, two paths are properly found.
The two routes found are
start->node1->node2->goal,
start->node2->node1->goal.
The correct routes are
start->node1->goal,
start->node2->goal.
Compare them. In the routes found, the flows collide at the node1-node2 edge, yet they pass each other and continue the search.
If we handle this behavior properly, we should obtain the correct routes.

Originally the water should collide and node1-node2 should be impassable. The routes found do not collide. But if we perform an operation that exchanges the water at the point of collision, we can reproduce the same behavior as a collision.
In start->node1->node2->goal, instead of going node1->node2, swap with the water that went node2->node1 in the other route start->node2->node1->goal, which used the cancel route.
Then the routes become start->node1->goal and start->node2->goal, which match the correct routes.
By adding the operation of creating cancel routes to the DFS and repeating the DFS in this way, we can find the set of routes that supports multiple agents.

Incidentally, we only need the number of turns to be minimal. Each agent's route does not need to be the shortest, and we only need to find any route that exists, so any path finding algorithm — BFS, Dijkstra, A*, and so on — can be used.

### Visualization with pygame
The visualization is done with pygame.
It is designed as a loop in which pressing specific keys switches screens.
Each coordinate is normalized to the screen size and recalculated.
This makes the hub size change per map, so the map is displayed at a size suited to each board. This improves the user experience.

## Resources
### Use of AI
The foundation of the code was all written by hand.
AI was used to resolve flake8 and mypy errors.
### References
- [Introduction to multi-agent path planning](https://kei18.github.io/note/posts/mapf-tutorial/)
- [Graph Theory lecture notes](https://ocw.hokudai.ac.jp/wp-content/uploads/2016/01/GraphTheory-2007-Note-all.pdf)
- [pygame documentation](https://www.pygame.org/docs/)
