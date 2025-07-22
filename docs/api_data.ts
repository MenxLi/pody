const ex_ip = "http://10.254.29.178:8799";
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
    url = url.slice(1);     // remove the leading slash
    let cmd = `pody ${method.toLowerCase()} ${url}`;
    for (let key in params) {
        const safeParam = params[key].match(/^[a-zA-Z0-9_\-\.,\:]+$/) ? params[key] : `"${params[key]}"`;
        cmd += ` ${key}:${safeParam}`;
    }
    return cmd;
}

export function fmtPodxCmd(_: string, url: string, params: Record<string, string>) {
    url = url.slice(1);     // remove the leading slash
    let cmd = `podx ${url}`;
    for (let key in params) {
        const safeParam = params[key].match(/^[a-zA-Z0-9_\-\.,\:]+$/) ? params[key] : `"${params[key]}"`;
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
            optional?: boolean,
        }
    },
    example?: {
        input: Record<string, string>,
        description?: string | null,
        output?: string | null | Object
    }
}

const apiData: { [key: string]: APIDescription } ={

    // pod endpoints ========================================
    "/user/info": {
        method: "GET",
        description: "Get the information of the user",
        example: {
            input: {},
            output: {
                "user": { "name": "limengxun", "is_admin": 0 },
                "quota": { "max_pods": 3, "gpu_count": 2, "memory_limit": -1, "storage_size": -1, "shm_size": -1 }
            }
        }
    }, 
    "/user/list": {
        method: "GET",
        description: "List all usernames in this node",
        example: {
            input: {},
            output: ['limengxun', 'lijiayu', 'wuji']
        }
    }, 
    "/user/ch-passwd": {
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

    "/pod/inspect": {
        method: "GET",
        description: "Get the information of a pod",
        parameters: {
            ins: {
                type: "string",
                description: "The instance to get information"
            }
        },
        example: {
            input: {ins: "test"},
            output: {'container_id': '014031e97c87', 'name': 'limengxun-test', 'status': 'running', 'image': 'exp:latest', 'port_mapping': ['20806:22', '20299:8000'], 'gpu_ids': [], "memory_limit": -1, "shm_size": 8589934592}
        }
    },

    "/pod/list": {
        method: "GET",
        description: "List all pods for the user",
        example: {
            input: {},
            output: `(A list of all pod names for the user)`
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
        example: {
            input: {ins: "myins"},
            output: `{log: " * Restarting OpenBSD Secure Shell server sshd..."}`
        }
    }, 
    "/pod/exec": {
        method: "POST",
        description: 
            "Execute a command in a pod, the command will be executed as root user using bash. " +
            "The default timeout is 30 seconds, long-running task will be terminated after the timeout. " +
            "If you want to run a long-running task, please set the timeout to a larger value.", 
        parameters: {
            ins: {
                type: "string",
                description: "The instance id of the pod to execute command"
            }, 
            cmd: {
                type: "string",
                description: "The command to execute"
            }, 
            timeout: {
                type: "number",
                description: "The timeout of the command in seconds",
                optional: true
            }
        },
        example: {
            input: {ins: "myins", cmd: "pwd"},
            output: {'exit_code': 0, 'log': '/workspace\r\n'}
        }
    }, 

    "/pod/commit": {
        method: "POST",
        description: "Commit a pod to an image, the image will be saved as <pody-commit-prefix>:<username>[-<tag>]. " + 
            "Note there are restrictions for image size and number of committed images for each user, " +
            "please refer to the user quota for more details. ", 
        parameters: {
            ins: {
                type: "string",
                description: "The instance id of the pod to commit"
            }, 
            tag: {
                type: "string",
                description: "The tag of the image to commit", 
                optional: true
            }, 
            msg: {
                type: "string",
                description: "The commit message, this will be used as the image comment", 
                optional: true 
            }
        },
        example: {
            input: {ins: "myins", tag: "latest"},
            output: {
                'image_name': 'pody-commit:limengxun-latest',
                'log': 'Container myins committed to image: pody-commit:limengxun-latest'
            }
        }
    },

    // image endpoints ========================================
    "/image/list": {
        method: "GET",
        description: "List all available images. " + 
            "The user committed images will omit the image name, leaving only the <username>-<tag>. ", 
        example: {
            input: {},
            output: `['limengxun-cu126_base', 'captain-cuda:12.6.3-cudnn-devel-ubuntu22.04']`
        }
    },

    "/image/inspect": {
        method: "GET",
        description: "Get the information of an image",
        parameters: {
            image: {
                type: "string",
                description: "The image to inspect, should be a full image name. " 
            }, 
        },
        example: {
            input: {image: "limengxun-latest"},
            output: {
                'name': 'pody-commit:limengxun-latest',
                'id': 'sha256:b9dbbd6961b98d2e489076b876dcb6fff37a57265b379066f7730cf8578aed05',
                'tags': ['pody-commit:limengxun-latest'],
                'comment': '',
                'size': 28695585758,
                'exposed_ports': {'22/tcp': {}, '8000/tcp': {}},
                'created': '2025-07-21T13:29:07.17395499Z'
            }
        }
    }, 

    "/image/delete": {
        method: "POST",
        description: "Delete a user committed image, please be careful, this operation is irreversible",
        parameters: {
            image: {
                type: "string",
                description: "The image to delete, can only be user commit images. "
            }
        },
        example: {
            input: {image: "limengxun"},
            output: {'log': 'Image pody-commit:limengxun deleted'}
        }
    },
    
    // statistics endpoints ========================================
    "/stat/cputime": {
        method: "GET",
        description: "Get the CPU time of the user(s) in seconds. " + 
            "The time is calculated using the [user CPU time] + [system CPU time] of all processes by the user(s) ", 
        parameters: {
            "user": {
                type: "string",
                description: "The usernames to get CPU time for, can be a comma-separated list, " +
                "if not provided, will include all users", 
                optional: true
            }, 
            "t": {
                type: "string",
                description: "The start time of the process to include in the statistics, " +
                "should be like: 1y, 1w, 1d, 1h, 1s, or a timestamp in seconds. " +
                "If not provided, will include all time ranges. ",
                optional: true
            }
        },
        example: {
            input: {user: "limengxun,lijiayu", t: "1w"},
            output: {
                "limengxun": 1234567.89,
                "lijiayu": 9876543.21
            }
        }
    },

    "/stat/gputime": {
        method: "GET",
        description: "Get the (rough) GPU time of the user(s) in seconds. " +
            "The time is calculated as [the number of GPUs used] * [the time the GPU is used] for all processes by the user(s)",
        parameters: {
            "user": {
                type: "string",
                description: "The usernames to get GPU time for, can be a comma-separated list, " +
                "if not provided, will include all users. ",
                optional: true
            }, 
            "t": {
                type: "string",
                description: "The start time of the process to include in the statistics, " +
                "should be like: 1y, 1w, 1d, 1h, 1s, or a timestamp in seconds. " +
                "If not provided, will include all time ranges", 
                optional: true
            }
        },
        example: {
            input: {user: "limengxun,lijiayu", t: "1w"},
            output: {
                "limengxun": 1234567.89,
                "lijiayu": 9876543.21
            }
        }
    },

    // resource endpoints ========================================
    "/host/gpu-ps": {
        method: "GET",
        description: "Get the process list running on the GPU(s)",
        parameters: {
            "id": {
                type: "string",
                description: "The id(s) of the GPU, multiple ids can be separated by comma", 
                optional: true
            }
        },
        example: {
            input: {'id': "0,1"},
            output: {
                "0": [
                    {
                        "pid": 3936, "pod": "limengxun-main", "cmd": "python -m ...", 
                        "uptime": 2309249.4564814568, "memory_used": 709079040, "gpu_memory_used": 721420288
                    }
                ],
                "1": [
                    {
                        "pid": 28963, "pod": "lijiayu-exp", "cmd": "/home/user/miniconda3/envs/vllm/bin/python -c from multiprocessing.spawn ...",
                        "uptime": 1446117.9469604492, "memory_used": 8506048512, "gpu_memory_used": 22248685568
                    }
                ]
            }
        }
    },

    "/host/spec": {
        method: "GET",
        description: "Get the specification of the node",
        example: {
            input: {},
            output: {
                'pody_version': '0.1.10',
                'docker_version': '26.1.5-ce',
                'nvidia_driver_version': '550.78',
                'nvidia_ctk_version': 'NVIDIA Container Toolkit CLI version 1.17.5 commit:...'
            }
        }
    }, 

    "/help": {
        method: "GET",
        description: "Get the help for a endpoint",
        parameters: {
            "path": {
                type: "string",
                description: "The path to get help for"
            }
        },
        example: {
            input: {path: "/pod/create"},
            output:[
                {
                    'path': '/pod/create',
                    'methods': ['POST'],
                    'params': [{'name': 'ins', 'optional': false}, {'name': 'image', 'optional': false}]
                }
            ] 
        } 
    },

    "/version": {
        method: "GET",
        description: "Get the version of the API",
    }
}

export default apiData;