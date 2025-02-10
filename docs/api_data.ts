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

const api_data: { [key: string]: APIDescription } ={
    "/pod/restart": {
        "method": "POST",
        "description": "Restart a pod",
        "parameters": {
            "tag": {
                "type": "string",
                "description": "The tag of the pod to restart, the actual pod name will be " + `<${ex_username}>-<tag>`
            }
        },
        "example": {
            "description": "Restart a pod named " + `${ex_username}-mytag`,
            "input": `${cmd} -X POST ${ex_username}:${ex_password} ${ex_ip}/pod/restart?tag=mytag`,
        }
    }, 
    "/pod/stop": {
        "method": "POST",
        "description": "Stop a pod",
        "parameters": {
            "tag": {
                "type": "string",
                "description": "The tag of the pod to stop, the actual pod name will be " + `<${ex_username}>-<tag>`
            }
        },
        "example": {
            "description": "Stop a pod named " + `${ex_username}-mytag`,
            "input": `${cmd} -X POST ${ex_ip}/pod/stop?tag=mytag`,
            "output": null
        }
    },
    "/pod/start": {
        "method": "POST",
        "description": "Start a pod",
        "parameters": {
            "tag": {
                "type": "string",
                "description": "The tag of the pod to start, the actual pod name is " + `<${ex_username}>-<tag>`
            }
        },
        "example": {
            "description": "Start a pod named " + `${ex_username}-mytag`,
            "input": `${cmd} -X POST ${ex_ip}/pod/start?tag=mytag`,
            "output": null
        }
    },
}

export default api_data;