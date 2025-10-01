# Constants for command structure

list_of_commands = [
    "add_stone",
    "add_base",
    "spatial_move",
    "attack",
    "tag",
    "timejump",
    "pass"
    ]

integer_command_keywords = [
        "stone_ID",
        "t",
        "x",
        "y",
        "a",
        "target_t",
        "target_x",
        "target_y",
        "target_a",
        "swap_effect"
    ]

# command_keywords[command type] = [ordered list of keywords present]
command_keywords = {
    "add_stone" : ["faction", "stone_type", "x", "y", "a"],
    "add_base" : ["faction", "x", "y"],
    "spatial_move" : ["stone_ID", "t", "x", "y", "target_x", "target_y", "target_a"],
    "attack" : ["stone_ID", "t", "x", "y", "target_t", "target_x", "target_y", "choice_keyword"],
    "tag" : ["stone_ID", "t", "x", "y", "choice_keyword"],
    "timejump" : ["stone_ID", "t", "x", "y", "target_t", "target_x", "target_y", "target_a", "swap_effect"],
    "pass" : ["stone_ID", "t", "x", "y"]
    }

# compress string vals[command keyword] = list of possible values, which will be encoded by their index
allowed_command_string_vals = {
    "type" : [
        "add_stone",
        "add_base",
        "spatial_move",
        "attack",
        "tag",
        "timejump",
        "pass"
        ],
    "faction" : [
        "A",
        "B",
        "GM",
        "neutral"
        ],
    "stone_type" : [
        "tank",
        "bombardier",
        "tagger",
        "sniper",
        "wildcard",
        "box",
        "mine"
        ],
    "choice_keyword" : [
        "lock",
        "unlock",
        "hide"
        ]
    }

