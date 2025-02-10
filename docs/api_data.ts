const ex_ip = "http://10.256.1.10";
const ex_username = "username";
const ex_password = "password";

export interface APIDescription {
    method: "GET" | "POST",
    description: string,
    parameters: {
        [key: string]: {
            type: string,
            description: string
        }
    },
    example: {
        input: string, 
        description?: string | null,
        output?: string | null
    }
}

const cmd = `curl -u ${ex_username}:${ex_password}`;

const apiData: { [key: string]: APIDescription } ={

    // pod endpoints ========================================
    "/pod/start": {
        method: "POST",
        description: "Start a pod",
        parameters: {
            tag: {
                type: "string",
                description: "The tag of the pod to start, the actual pod name is " + `<${ex_username}>-<tag>`
            }
        },
        example: {
            "input": `${cmd} -X POST ${ex_ip}/pod/start?tag=mytag`,
        }
    },
    "/pod/stop": {
        method: "POST",
        description: "Stop a pod",
        parameters: {
            tag: {
                type: "string",
                description: "The tag of the pod to stop, the actual pod name will be " + `<${ex_username}>-<tag>`
            }
        },
        example: {
            input: `${cmd} -X POST ${ex_ip}/pod/stop?tag=mytag`,
        }
    },
    "/pod/restart": {
        method: "POST",
        description: "Restart a pod",
        parameters: {
            tag: {
                type: "string",
                description: "The tag of the pod to restart, the actual pod name will be " + `<${ex_username}>-<tag>`
            }
        },
        example: {
            input: `${cmd} -X POST ${ex_username}:${ex_password} ${ex_ip}/pod/restart?tag=mytag`,
        }
    }, 

    // resource endpoints ========================================
    "/resource/gpu-ps": {
        method: "GET",
        description: "Get the process list of the GPU",
        parameters: {
            id: {
                type: "string",
                description: "The id(s) of the GPU, multiple ids can be separated by comma"
            }
        },
        example: {
            input: `${cmd} ${ex_ip}/resource/gpu-ps?id=0,1`,
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