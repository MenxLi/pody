# Deploy

## Installation
First install the [docker](https://docs.docker.com/) and the [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

Then you can install the Pody server from pip:
```sh
pip install "pody[server]"
```

## Start the server
The server stores the data in `$PODY_HOME` directory, which is by default `~/.pody`.

To start the server:
```sh
pody-server --port 8799
```
Then by setting appropriate environment variables, 
you can use the [pody-cli](/pody-cli) to interact with the server.

## Managements

### Users
To manage users:
```sh
pody-user ...
```
Please refer to `--help` for more information.

### Configurations
The server configuration is stored in `$PODY_HOME/config.toml` file. 
There are comments in the file to help you understand the options. 

For example, to manage images, you should first pull or build the image, 
then you can specify the images to expose to the client by editing the `[[images]]` section in the
`$PODY_HOME/config.toml` file.
