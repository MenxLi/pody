---
outline: deep
---

# Deploy

## Installation
First install the [docker](https://docs.docker.com/) and the [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

Then you can install the Pody server from pip:
```sh
pip install "pody[server]"
```

:::tip 
If you run the server as a non-root user, please add the user to the `docker` group.   
For details, refer to the [Docker documentation (linux-postinstall)](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user).
:::

## Start the server
The server stores the data in `$PODY_HOME` directory, which is by default `~/.pody`.

To start the server:
```sh
pody-server --port 8799
```
Then by setting appropriate environment variables, 
you can use the [pody-cli](/pody-cli) to interact with the server.

:::tip
You can use `systemd` to start the server on boot. For details, refer to the [start on boot guide](./start_on_boot.md).
:::

## Managements

### Users and quotas
To manage users:
```sh
pody-user ...
```

To manage user quotas:
```sh
pody-quota ...
```
Please refer to `--help` for more information.

### Configurations
The server configuration is stored in `$PODY_HOME/config.toml` file. 
There are comments in the file to help you understand the options. 

For example, to manage images, you should first pull or build the image, 
then specify the images to expose to the client by editing the `[[images]]` section in the
`$PODY_HOME/config.toml` file.

For a more detailed introduction, see the [configuration guide](./configuration).

### Optional: Using docker network
If you want to allow containers to communicate with each other in a dedicated network (with DNS resolution), 
you can create a user-defined docker network (e.g. `pody-net`) and specify it in the container configuration.
```sh
docker network create pody-net
```
then, set the `network` option in the congfiguration file:
```toml
network = "pody-net"
```
