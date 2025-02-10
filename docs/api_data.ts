const ex_ip = "http://10.256.1.10";
const ex_username = "username";
const ex_password = "password";

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
        input: string, 
        description?: string | null,
        output?: string | null
    }
}

const cmd = `curl -u ${ex_username}:${ex_password}`;

const apiData: { [key: string]: APIDescription } ={

    // pod endpoints ========================================
    "/pod/create": {
        method: "POST",
        description: "Create a new pod",
        parameters: {
            tag: {
                type: "string",
                description: "The tag of the pod to create, the actual pod name will be " + `<${ex_username}>-<tag>`
            }, 
            image: {
                type: "string",
                description: "The image of the pod to create from (e.g. ubuntu2204-cuda12.1:latest)"
            }
        },
        example: {
            input: `${cmd} -X POST \\\n\t"${ex_ip}/pod/create?tag=mytag&image=ubuntu2204-cuda12.1:latest"`,
            output: `(The output should be the pod info in json)`
        }
    }, 

    "/pod/delete": {
        method: "POST",
        description: "Delete a pod. Please be careful, this operation is irreversible",
        parameters: {
            tag: {
                type: "string",
                description: "The tag of the pod to delete"
            }
        }
    },

    "/pod/info": {
        method: "GET",
        description: "Get the information of a pod",
        parameters: {
            tag: {
                type: "string",
                description: "The tag of the pod to get information"
            }
        },
        example: {
            input: `${cmd} \\\n\t${ex_ip}/pod/info?tag=mytag`,
            output: `(TO BE FILLED)`
        }
    },

    "/pod/list": {
        method: "GET",
        description: "List all pods for the user",
        example: {
            input: `${cmd} \\\n\t${ex_ip}/pod/list`,
            output: `(A list of all pods for the user)`
        }
    },


    "/pod/start": {
        method: "POST",
        description: "Start a pod",
        parameters: {
            tag: {
                type: "string",
                description: "The tag of the pod to start"
            }
        },
        example: {
            "input": `${cmd} -X POST \\\n\t${ex_ip}/pod/start?tag=mytag`,
            "output": `(Text output of the pod start command)`
        }
    },
    "/pod/stop": {
        method: "POST",
        description: "Stop a pod",
        parameters: {
            tag: {
                type: "string",
                description: "The tag of the pod to stop"
            }
        },
    },
    // "/pod/kill": {
    //     method: "POST",
    //     description: "Kill a pod, without doing any cleanup",
    //     parameters: {
    //         tag: {
    //             type: "string",
    //             description: "The tag of the pod to stop"
    //         }
    //     },
    // },
    "/pod/restart": {
        method: "POST",
        description: "Restart a pod",
        parameters: {
            tag: {
                type: "string",
                description: "The tag of the pod to restart"
            }
        },
    }, 

    // resource endpoints ========================================
    "/resource/images": {
        method: "GET",
        description: "List all available images",
        example: {
            input: `${cmd} \\\n\t${ex_ip}/resource/images`,
            output: `(A list of all available images)`
        }
    },

    "/resource/gpu-ps": {
        method: "GET",
        description: "Get the process list running on the GPU(s)",
        parameters: {
            id: {
                type: "string",
                description: "The id(s) of the GPU, multiple ids can be separated by comma"
            }
        },
        example: {
            input: `${cmd} \\\n\t${ex_ip}/resource/gpu-ps?id=0,1`,
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