# Configuration File

Pody stores its server configuration in a TOML file at `$PODY_HOME/config.toml`.
If `PODY_HOME` is not set, the default location is `~/.pody/config.toml`.

<!-- This file controls the server-side behavior of Pody, including:

- which ports can be assigned to containers
- which host volumes are mounted into containers
- which Docker network to use
- the default quota for users
- which images are exposed to clients
- whether remote user profile integration is enabled -->

## Edit the configuration

The easiest way to edit the file is:

```sh
pody-util config
```

If the configuration file does not exist yet, this command will create it from the
built-in default template and then open it in your editor.

By default, `pody-util config` uses `$EDITOR`, and falls back to `vi` if `$EDITOR`
is not set. You can also choose an editor explicitly:

```sh
pody-util config --editor nano
```

If you want to check where Pody stores its data and configuration files, run:

```sh
pody-util show-home
```

## Content and file structure

The generated file contains comments explaining each option. The most important
parts are:

- `available_ports`: host ports or port ranges that Pody can assign to containers
- `volume_mappings`: host paths or tmpfs mounts exposed inside containers
- `network`: an optional user-defined Docker network for inter-container communication
- `default_quota`: the fallback resource limits for users
- `[[images]]`: the list of images that clients are allowed to create pods from
- `remote_user_profile`: settings for remote user management integration ([more details](./remote_user_profile.md))

For most deployments, the first section to adjust is `[[images]]`, since it
defines which images are visible to users and which ports should be exposed for
each image.

## Typical workflow

A common setup flow looks like this:

1. Pull or build the Docker images you want to offer.
2. Open the configuration file with `pody-util config`.
3. Edit the `[[images]]` section to list those images.
4. Review `available_ports`, `volume_mappings`, and `default_quota`.
5. Set `network` if you want containers to join a dedicated Docker network.

For example:

```toml
available_ports = "20000-21000"
network = "pody-net"

[[images]]
name = "ubuntu2204-cu121-base:latest"
ports = [22, 8000]
```

In this example, Pody may allocate host ports from `20000-21000`, attach the
container to the `pody-net` network, and expose ports `22` and `8000`, mapping them to random ports in the specified range, for the specified image.


:::info 
- Invalid configuration values may prevent the server from loading correctly.
- Since the file includes inline comments, it is usually easiest to start from the
  generated default and edit it incrementally.
:::
