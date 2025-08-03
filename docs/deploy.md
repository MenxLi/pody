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

This command opens the configuration file in your default editor:
```sh
pody-util config
```

For example, to manage images, you should first pull or build the image, 
then specify the images to expose to the client by editing the `[[images]]` section in the
`$PODY_HOME/config.toml` file.

### Optional: Communicate between containers
If you want to allow containers to communicate with each other,
you can create a user-defined docker network (e.g. `pody-net`) and specify it in the container configuration.
```sh
docker network create pody-net
```
then, set the `network` option in the congfiguration file:
```toml
network = "pody-net"
```

## Start on boot
To start the server on boot, you can use the `pody-util systemd-unit` helper command to generate a systemd service content:
```sh
pody-util systemd-unit --port 8799
```
This will load the current environment variable settings, 
generate a systemd unit file for the Pody server using current user, 
and print the content to the standard output.
Should put the output to global systemd unit directory, e.g. 
```sh
pody-util systemd-unit | sudo tee /etc/systemd/system/pody.service
```
and enable it with: 
```sh
sudo systemctl daemon-reload && \
sudo systemctl enable pody.service && \
sudo systemctl start pody.service
```