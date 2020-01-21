#/bin/bash
#
# wispsDocMaker - customizeable driver to generate and publish WISPS docs
#
# This script sets a few environmental variables and invokes buildAndPush.
# Permissions should be set by these scripts in a way that allows more than
# one team member to push to the directories managed by the web server.  (The
# group should have write permission for the directories and files.)
#
# Note the environmental variable forceBuildAndPush.  The buildAndPush.sh
# generally takes no action if the development branch has not been changed.
# The variable forceBuildAndPush overrides that behavior.
#
export forceBuildAndPush="true"
export WEBUSER=eschlie
export webdirwisps='/mnt/project/users/wisps/'
cd ~/repositories/wisps/docs
chmod ug+x ./buildAndPushTemp.sh ./rsynchtml
./buildAndPushTemp.sh
