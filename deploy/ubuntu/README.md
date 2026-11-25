# On-demand Notes CLI on Ubuntu

This deployment targets Linux x86_64 and CPython 3.14. It runs one command and
exits. No daemon, timer, listening port, or password environment variable is used.
The container is limited to half a CPU and 512 MiB of memory. An idle deployment
has no running container. Keep the original Apple account login interactive.

## Reproduce the image

Use the exact source commit recorded in `artifact.json`. `build.lock` pins the
complete wheel-build tool environment. `requirements.lock` pins the locally built
PyiCloud wheel and every transitive runtime and CLI dependency, including actual
wheel SHA256 hashes. These locks are specific to the platform above.

The wheel archives are kept outside Git in `wheelhouse/`. Restore the archived
wheelhouse and verify `SHA256SUMS` before building. The separate
`build-wheelhouse/` contains the tools pinned in `build.lock` and is excluded
from the runtime image. Do not fall back to source
packages or an online index if a wheel is absent. From this directory, with the
fixed base image already present:

```sh
sha256sum -c SHA256SUMS
docker build --network=none --pull=false \
  --build-arg SOURCE_COMMIT=FULL_SOURCE_COMMIT \
  -t pyicloud-notes:FIXED_SOURCE_COMMIT .
docker image inspect pyicloud-notes:FIXED_SOURCE_COMMIT --format '{{.Id}}'
```

The fork was created without historical tags. When rebuilding the application
wheel from a fresh source clone, first restore the verified version anchor
locally, then check out the exact `source_commit` from `artifact.json`:

```sh
git tag 2026.11.2 292875b0c7e8c9deb54f5ec47cff3d1fcca2e58a
```

Do this only when that tag is absent; an existing tag must point to that same
commit. Build with the tools in `build.lock`, no build isolation or network,
and `SOURCE_DATE_EPOCH` from `artifact.json`. The version comes from
setuptools-scm and the restored Git tag; do not hand-edit a version number.

Set `PYICLOUD_IMAGE=sha256:...` in `.env` to the verified local image ID. This
prevents a mutable tag from silently selecting another image. Images built
locally have an image ID, not a registry manifest digest. Neither lock files nor
hashes prove that every third-party dependency has been audited.

## First use

The installed directory is `/srv/homelab/pyicloud/current`. Its `state` and
`exports` paths point to private persistent directories shared across releases.
For a fresh standalone checkout, create these as UID/GID 10001, mode 0700.

Run from a real interactive SSH terminal:

```sh
cd /srv/homelab/pyicloud/current
sudo docker compose run --rm notes --version
sudo docker compose run --rm notes auth login \
  --username 'YOUR_APPLE_ID' --session-dir /state
```

Enter the password and verification code only in the terminal. Answer **no** to
the password keyring prompt. The null keyring backend is enforced in the image;
it cannot store the password. For a mainland China iCloud account, add
`--china-mainland` to the login command. Account region is retained in local
metadata. Do not use `--password` on the command line or save it in `.env`.

Then list a few notes and read one note as text:

```sh
sudo docker compose run --rm notes notes recent \
  --username 'YOUR_APPLE_ID' --session-dir /state --limit 5
sudo docker compose run --rm notes notes get 'NOTE_ID' \
  --username 'YOUR_APPLE_ID' --session-dir /state
```

Session and trust tokens remain unencrypted in `state`, which must be protected
as credentials. Session expiry can require another interactive login. The
entrypoint removes `PYICLOUD_NOTES_DEBUG` and uses a private file creation mask.
Docker log storage is disabled; command output still appears in the terminal.
Avoid recording terminal sessions that contain private notes.

## Verification and limitations

Offline checks cover HTML rendering regressions, CLI startup, installed
dependencies, image identity, private file permissions, and container limits.
They do not establish successful Apple authentication or real Notes access.
Record those separately after interactive login. The general CLI also includes
write commands; use only the read commands shown above during initial acceptance.

No domain or destination-IP egress filter is installed. HTTP proxy settings
alone do not constrain the authentication WebSocket. Conditional attachment URL,
export path and payload-size risks from the audit remain; start with text reads
and avoid bulk attachment downloads. This is not a sandbox for hostile notes.

## Rollback

There is no always-running Notes service to stop. Select the previous release
with the `current` symlink and its pinned image ID; leave `state` and `exports`
intact. To retire the deployment, stop invoking the CLI and archive its directory.
Do not delete tokens or exports as part of an image rollback. Other Compose
projects and host firewall settings are independent of this deployment.
