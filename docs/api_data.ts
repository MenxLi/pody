const ex_ip = "http://10.256.1.10";
const ex_username = "username";
const ex_password = "password";

export function fmtCurlCmd(method: string, url: string, params: Record<string, string>)  {
    let cmd = `curl -u ${ex_username}:${ex_password} -X ${method} "${ex_ip}${url}`;
    if (Object.keys(params).length === 0) { return cmd + '"'; }
    else { cmd += "?"; }
    for (let key in params) {
        cmd += `${new URLSearchParams({[key]: params[key]}).toString()}`;
    }
    return cmd + '"';
}

export function fmtPodyCmd(method: string, url: string, params: Record<string, string>) {
    let cmd = `pody ${method.toLowerCase()} ${url}`;
    for (let key in params) {
        const safeParam = params[key].match(/^[a-zA-Z0-9_\-]+$/) ? params[key] : `"${params[key]}"`;
        cmd += ` ${key}:${safeParam}`;
    }
    return cmd;
}

export interface APIDescription {
    method: "GET" | "POST",
    description: string,
    parameters?: {
        [key: string]: {
            type: string,
            description: string
        }
    },
    example?: {
        input: Record<string, string>,
        description?: string | null,
        output?: string | null
    }
}

const apiData: { [key: string]: APIDescription } ={

    // pod endpoints ========================================
    "/user/info": {
        method: "GET",
        description: "Get the information of the user",
        parameters: {},
        example: {
            input: {},
            output: `{
    "user": {
        "name": "limengxun",
        "is_admin": 0
    },
    "quota": {
        "max_pods": -1,
        "gpu_count": -1,
        "memory_limit": -1
    }
}`
        }
    }, 
    "/user/list": {
        method: "GET",
        description: "List all usernames and their admin status in this node",
        parameters: {},
    }, 
    "/user/ch-password": {
        method: "GET",
        description: "List all usernames and their admin status in this node",
        parameters: {
            passwd: {
                type: "string",
                description: "The new password"
            }
        },
    }, 
    "/pod/create": {
        method: "POST",
        description: "Create a new pod",
        parameters: {
            ins: {
                type: "string",
                description: "The instance to create, the actual pod name will be " + `<${ex_username}>-<ins>`
            }, 
            image: {
                type: "string",
                description: "The image of the pod to create from (e.g. ubuntu2204-cuda12.1:latest)"
            }
        },
        example: {
            input: {ins: "myins", image: "ubuntu2204-cuda12.1:latest"},
            output: `(The output should be the pod info in json)`
        }
    }, 

    "/pod/delete": {
        method: "POST",
        description: "Delete a pod. Please be careful, this operation is irreversible",
        parameters: {
            ins: {
                type: "string",
                description: "The instance to delete"
            }
        }
    },

    "/pod/info": {
        method: "GET",
        description: "Get the information of a pod",
        parameters: {
            ins: {
                type: "string",
                description: "The instance to get information"
            }
        },
        example: {
            input: {ins: "myins"},
            output: `(TO BE FILLED)`
        }
    },

    "/pod/list": {
        method: "GET",
        description: "List all pods for the user",
        example: {
            input: {},
            output: `(A list of all pods for the user)`
        }
    },


    "/pod/start": {
        method: "POST",
        description: "Start a pod",
        parameters: {
            ins: {
                type: "string",
                description: "The instance to start"
            }
        },
        example: {
            "input": {ins: "myins"},
            "output": `(Text output of the pod start command)`
        }
    },
    "/pod/stop": {
        method: "POST",
        description: "Stop a pod",
        parameters: {
            ins: {
                type: "string",
                description: "The instance to stop"
            }
        },
    },
    "/pod/restart": {
        method: "POST",
        description: "Restart a pod",
        parameters: {
            ins: {
                type: "string",
                description: "The instance to restart"
            }
        },
    }, 
    "/pod/exec": {
        method: "POST",
        description: "Execute a command in a pod",
        parameters: {
            ins: {
                type: "string",
                description: "The instance id of the pod to execute command"
            }, 
            cmd: {
                type: "string",
                description: "The command to execute"
            }
        },
    }, 

    // resource endpoints ========================================
    "/resource/images": {
        method: "GET",
        description: "List all available images",
        example: {
            input: {},
            output: `(A list of all available images)`
        }
    },

    "/resource/gpu-ps": {
        method: "GET",
        description: "Get the process list running on the GPU(s)",
        parameters: {
            "gpu-id": {
                type: "string",
                description: "The id(s) of the GPU, multiple ids can be separated by comma"
            }
        },
        example: {
            input: {'gpu-id': "0,1"},
            output: `\
{
    "0": [
        {
            "pid": 3936,
            "pod": "limengxun-main",
            "cmd": "python -m ...",
            "uptime": 2309249.4564814568,
            "memory_used": 709079040,
            "gpu_memory_used": 721420288
        }
    ],
    "1": [
        {
            "pid": 28963,
            "pod": "lijiayu-exp",
            "cmd": "/home/user/miniconda3/envs/vllm/bin/python -c from multiprocessing.spawn ...",
            "uptime": 1446117.9469604492,
            "memory_used": 8506048512,
            "gpu_memory_used": 22248685568
        }
    ]
}
`
        }
    },
}

export default apiData;