
# Copyright 2020 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import logging
import random
from flask import Flask, request

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = Flask(__name__)
moves = ['F', 'T', 'L', 'R']

@app.route("/", methods=['GET'])
def index():
    return "Let the battle begin!"

@app.route("/", methods=['POST'])
def move():
    request.get_data()
    logger.info(request.json)

    mybot_url = request.json['_links']['self']['href']
    dims = request.json['arena']['dims']
    bot_state_map = request.json['arena']['state']

    # {'x': 0, 'y': 6, 'direction': 'S', 'wasHit': False, 'score': -185}
    my_state = bot_state_map[mybot_url]
    was_hit = my_state['wasHit']

    # N E W S
    x = my_state['x']
    y = my_state['y']

    direction_attack_range_map = {
        'N': {
            'can_attack_dims': [[x, y-1], [x, y-2], [x, y-3]],
            'possible_attack_dims_with_direction': [[x, y-4, 'S'], [x+1, y-1, 'W'], [x+1, y-2, 'W'], [x+1, y-3, 'W'], [x-1, y-1, 'E'], [x-1, y-2, 'E'], [x-1, y-3, 'E']],
            'move_attack_dims': [x, y-4],
            'move_to': [x, y-1]
        },
        'E': {
            'can_attack_dims': [[x+1, y], [x+2, y], [x+3, y]],
            'possible_attack_dims_with_direction': [[x+4, y, 'W'], [x+1, y+1, 'N'], [x+2, y+1, 'N'], [x+3, y+1, 'N'], [x+1, y-1, 'S'], [x+2, y-1, 'S'], [x+3, y-1, 'S']],
            'move_attack_dims': [x+4, y],
            'move_to': [x+1, y]
        },
        'W': {
            'can_attack_dims': [[x-1, y], [x-2, y], [x-3, y]],
            'possible_attack_dims_with_direction': [[x-4, y, 'E'], [x-1, y+1, 'N'], [x-2, y+1, 'N'], [x-3, y+1, 'N'], [x-1, y-1, 'S'], [x-2, y-1, 'S'], [x-3, y-1, 'S']],
            'move_attack_dims': [x-4, y],
            'move_to': [x-1, y]
        },
        'S': {
            'can_attack_dims': [[x, y+1], [x, y+2], [x, y+3]],
            'possible_attack_dims_with_direction': [[x, y+4, 'N'], [x+1, y+1, 'W'], [x+1, y+2, 'W'], [x+1, y+3, 'W'], [x-1, y+1, 'E'], [x-1, y+2, 'E'], [x-1, y+3, 'E']],
            'move_attack_dims': [x, y+4],
            'move_to': [x, y+1]
        },
    }

    action_weight_map = {
        'F': 0, 'T': 0, 'L': 0, 'R': 0
    }
    can_i_move = True
    move_to = direction_attack_range_map[my_state['direction']]['move_to']
    for url, state in bot_state_map.items():
        if url == mybot_url:
            continue

        if [state['x'], state['y']] in direction_attack_range_map[my_state['direction']]['can_attack_dims']:
            return 'T'

        calculate_wight(state['x'], state['y'], state['direction'], my_state, action_weight_map, direction_attack_range_map)
        if [state['x'], state['y']] == move_to:
            can_i_move = False

    logger.info(action_weight_map)

    if move_to[0] <= 0 or move_to[1] <= 0 or move_to[0] >= (dims[0] - 2) or move_to[1] >= (dims[1] - 2):
        can_i_move = False

    # weighted_moves = [k for k, v in sorted(a.items(), key=lambda item: item[1], reverse=True)]
    for move, weight in sorted(action_weight_map.items(), key=lambda item: item[1], reverse=True):
        if move == 'F' and can_i_move == False:
            continue
        if was_hit == True and move == 'T' and weight <= 4:
            continue
        if move == 'T' and weight == 0:
            continue
        return move

    if 'N' == my_state['direction']:
        return 'R' if x < (dims[0] / 2) else 'L'
    elif 'E' == my_state['direction']:
        return 'L' if y < (dims[1] / 2) else 'R'
    elif 'W' == my_state['direction']:
        return 'R' if y < (dims[1] / 2) else 'L'
    else:
        return 'L' if x < (dims[0] / 2) else 'R'

    return moves[random.randrange(len(moves))]


def calculate_wight(x, y, direction, my_state, action_weight_map, direction_attack_range_map):
    if [x, y, direction] in direction_attack_range_map[my_state['direction']]['possible_attack_dims_with_direction']:
        action_weight_map['T'] += 1

    if [x, y] == direction_attack_range_map[my_state['direction']]['move_attack_dims']:
        action_weight_map['F'] += 1

    turn_right_direction = None
    turn_left_direction = None
    if 'N' == my_state['direction']:
        turn_right_direction = 'E'
        turn_left_direction = 'W'
    elif 'E' == my_state['direction']:
        turn_right_direction = 'S'
        turn_left_direction = 'N'
    elif 'W' == my_state['direction']:
        turn_right_direction = 'N'
        turn_left_direction = 'S'
    else:
        turn_right_direction = 'W'
        turn_left_direction = 'E'

    if [x, y] in direction_attack_range_map[turn_right_direction]['can_attack_dims']:
        action_weight_map['R'] += 1

    if [x, y] in direction_attack_range_map[turn_left_direction]['can_attack_dims']:
        action_weight_map['L'] += 1


if __name__ == "__main__":
    app.run(debug=False,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))

