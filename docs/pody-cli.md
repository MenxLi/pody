# Pody client utility

Pody CLI is a command-line tool that allows you to interact with the Pody API from client side. 
The utility is written in Python and can be installed using `pip`:

```sh
pip install pody
```

## Configuration
The authentication is done by setup the environment variables `PODY_API_BASE`, `PODY_USERNAME` and `PODY_PASSWORD`.  
One way to do this is to set them in your shell profile file (e.g. `.bashrc`, `.zshrc`):

```sh
export PODY_API_BASE="http://localhost:5000"
export PODY_USERNAME="username"
export PODY_PASSWORD="password"
```

Another way is to use a configuration file, e.g. you can create a directory to store your credentials:

```sh
mkdir -p ~/pody-credentials
vi ~/pody-credentials/node1.sh     # set the variables as above
```

Then you can source the file in your shell profile to login to the server 😊🚀:
```sh
source ~/pody-credentials/node1.sh
```

The latter method is more flexible and allows you to switch between different servers easily.

## Make requests
The most basic usage of the utility is to make requests to the Pody API. 
The usage mostly follows folloiwing pattern:
```sh
pody [METHOD] [ROUTE] [OPTIONS...]
```

For example, to [restart a pod](./api.md#pod-restart) you can run:
```sh
pody post pod/restart ins:myins
```

The method is not strictly a HTTP method, it can be one of `get`, `post`, `fetch`. 
Notebly, `fetch` is used to automatically select appropriate method based on the route. 
So the above command can be written as:
```sh
pody fetch pod/restart ins:myins
```

### Podx
`pody fetch` is the most used command, 
a simple shorthand `podx` is provided for it. 
Which means `podx ...` is equivalent to `pody fetch ...`. 
The above command can be written as: 
```sh
podx pod/restart ins:myins
```

## High-level Utilities
In addition to the above, the subcommand of `pody` also contains some higher-level utilities, 
namely `copy-id` and `stat`.

---
The `copy-id` command is used to copy your public key to the server,
enabling SSH access to the containers: 
```sh
pody copy-id instance_name [pub_key_path]
```

---
The `stat` command is used to get the statistics of the server. 
Now support `cputime` and `gputime`, for example: 
```sh
pody stat gputime 1w
```
This will return the (rough) GPU time usage of the server in the last week, 
or you can omit the time limit to get the total time usage. 


## More Helpers
Moreover, the utility provides a `help` command to list all available routes and their parameters:

You can use `help` to get help on a specific route, or a subset of routes:
```sh
pody help pod/restart
pody help pod/
```

:::details Example
```sh
pody help user/
```
```txt
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┓
┃ Path            ┃ Methods ┃ Params ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━┩
│ /user/info      │ GET     │        │
│ /user/list      │ GET     │        │
│ /user/ch-passwd │ POST    │ passwd │
└─────────────────┴─────────┴────────┘
```
:::

:::tip
The `get/post/fetch` methods, when applied to a route, will invoke the `help` method instead,  
*i.e.* `pody get user/` or `podx user/` will invoke `pody help user/` and show the parameters.
:::

---
Lastly, to get the version of the CLI tools, you can use the `version` command:
```sh
pody version
```
You should use this command to check if the utility version is in sync with the server version. 
In addition, you can use: 
```sh
pody version --changelog
```
to see the changelog of the software.

**Please always use `--help` to see the details of each command.**