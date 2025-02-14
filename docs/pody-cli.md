# Pody client utility

Pody client CLI utility is a command-line tool that allows you to interact with the Pody API. 
It act like `curl` but is more fiendly for Pody API.  

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

Another way is to use a configuration files, e.g. you can create a directory to store your credentials:

```sh
mkdir -p ~/.pody-credentials
vi ~/.pody-credentials/node1.sh     # set the variables as above
```

Then you can source the file in your shell profile to login to the server 😊🚀:
```sh
source ~/.pody-credentials/node1.sh
```

The latter method is more flexible and allows you to switch between different servers easily.

## Usage
The usage follows folloiwing pattern:
```sh
pody [METHOD] [ROUTE] [OPTIONS...]
```

For example, to [restart a pod](./api.md#pod-restart) you can run:
```sh
pody post /pod/restart ins:myins
```

The method is not strictly a HTTP method, it can be one of `get`, `post`, `fetch`, `help`. 
Notebly, `fetch` is used to automatically select appropriate method based on the route. 
So the above command can be written as:
```sh
pody fetch /pod/restart ins:myins
```

You can also use `help` to get help on a specific route, or a subset of routes:
```sh
pody help /pod/restart
pody help /pod/
```