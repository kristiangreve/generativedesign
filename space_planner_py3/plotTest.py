import json, random
from space_planning import get_layout
import matplotlib.pyplot as plt


json_path = "room_data.json"
with open(json_path, 'rb') as f:
    definition = json.loads(f.read())
    room_def = definition["rooms"]

num_rooms = len(room_def)

split_list = [random.random() for i in range(num_rooms-2)]
dir_list = [int(round(random.random())) for i in range(num_rooms-1)]
room_order = list(range(num_rooms))
random.shuffle(room_order)

min_opening = 3

print("\nINPUTS:")
print("split list:", [round(s, 2) for s in split_list])
print("split direction:", dir_list)
print("room order:", room_order)

edges_out, adjacency_score, aspect_score = get_layout(room_def, split_list, dir_list, room_order, min_opening)
print('Edges out: ', edges_out)


max_lines = 3
lines = 0

for pair in edges_out:
    print('Coord 1:', pair[0], "Coord 2:", pair[1])
    plt.plot(pair[0],pair[1])
    lines += 1
    if lines > max_lines:
        break
#plt.plot([x1,x2],[y1,y2])
plt.show()
