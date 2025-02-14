# Deploy

## Installation
First install the [docker](https://docs.docker.com/) and the [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

Then you can install the Pody server from pip:
```sh
pip install "pody[server]"
```

## Usage
The server stores the data in `$PODY_HOME` directory, which is by default `~/.pody`.

To start the server:
```sh
pody-server
```

To manage users:
```sh
pody-user ...
```
Please refer to `--help` for more information.

To manage images, you should first pull or build the image, 
then you can specify the images to expose to the client by editing the `$PODY_HOME/config.toml` file.
