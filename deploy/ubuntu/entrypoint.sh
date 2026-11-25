#!/bin/sh
set -eu
umask 077
unset PYICLOUD_NOTES_DEBUG
exec icloud "$@"
