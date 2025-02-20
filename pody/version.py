
VERSION_HISTORY = {
    "0.1.9": [
        "Improve help route, format help output as table", 
    ], 
    "0.1.10": [
        "Remove /status route, add /host/spec and /version routes", 
    ], 
    "0.1.11": [
        "Use sqlite for logging", 
        "Add version client command",
        "Improve response for duplicate pod creation",
    ],
}

VERSION = tuple([int(x) for x in list(VERSION_HISTORY.keys())[-1].split('.')])