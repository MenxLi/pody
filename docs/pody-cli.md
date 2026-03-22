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
The most common way to call the Pody API is with `podx`:
```sh
podx [ROUTE] [OPTIONS...]
```

For example, to [restart a pod](./api.md#pod-restart):
```sh
podx pod/restart ins:myins
```

For raw request commands, parameters are passed as `key:value` pairs. In the
example above, `ins:myins` means the `ins` parameter is set to `myins`.

`podx` is a shorthand for `pody fetch`. The `fetch` mode automatically chooses
the appropriate HTTP method for the route, so in most cases you do not need to
think about whether the underlying request is `GET` or `POST`.

If you do want to specify the method explicitly, use `pody` directly:
```sh
pody [METHOD] [ROUTE] [OPTIONS...]
```

`METHOD` can be `get`, `post`, or `fetch`. For example, the `podx` command above is equivalent to:
```sh
pody fetch pod/restart ins:myins
```
This will automatically use the `POST` method, since `pod/restart` is a mutating route.

## High-level Utilities
In addition to the above, the subcommand of `pody` also contains some higher-level utilities, 
namely `copy-id`, `connect`, and `stat`.

---
The `copy-id` command is used to copy your public key to the server,
enabling SSH access to the containers: 
```sh
pody copy-id instance_name [pub_key_path]
```
Omitting the `pub_key_path` will use the default path.

---
The `connect` command is a shortcut used to connect to the pods via SSH:
```sh
pody connect instance_name [-u USERNAME] [-i IDENTITY_FILE] [-t]
```
Where `-u` specifies the SSH username (default is `root`), 
`-i` specifies the identity file (private key) to use, 
and `-t` enables temporary access (disables host key checking).

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