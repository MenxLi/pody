
# Start on boot
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