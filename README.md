# Cosmos State Exports

A service to export the state of CosmosSDK chain nodes.

**Pairs with** - https://github.com/Reecepbcups/exports-api

**Example** - https://exports.reece.sh

# Setup
```sh
# install base packages for the super user
sudo pip install -r requirements.txt

cp config.example.json config.json # then modify to your needs

# NOTES:
# - SDK v45 chains:
#   - require [] for modules to export.
#   - typically use 1> for output
# - SDK v46+ chains:
#   - can specific modules such as ["bank", "auth", "gov"] etc...
#   - typically use > for output


# Setup in a schedule
sudo crontab -e

# the script must run as sudo to access the node's data directory
# if you run the node as root, but interact with a user account.

# Run All:
0 2 * * * sudo /usr/bin/python3 /home/user/snapshot.py

# OR Run specific
0 2 * * * sudo /usr/bin/python3 /home/user/snapshot.py gaia,juno,terra...
```
