FROM python@sha256:22eafb370920ad8b429e0aec3fff433e0669968519f5d60469d83729c138b28b

ARG SOURCE_COMMIT
LABEL org.opencontainers.image.source="https://github.com/mental1104/pyicloud" \
      org.opencontainers.image.revision="${SOURCE_COMMIT}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring \
    HOME=/state \
    USER=notes \
    LOGNAME=notes

COPY requirements.lock /install/requirements.lock
COPY wheelhouse/ /install/wheelhouse/
RUN python -m pip --isolated install --no-index --find-links=/install/wheelhouse \
      --only-binary=:all: --require-hashes -r /install/requirements.lock \
    && python -m pip check \
    && rm -rf /install
COPY --chmod=0555 entrypoint.sh /usr/local/bin/notes-entrypoint

USER 10001:10001
WORKDIR /exports
ENTRYPOINT ["notes-entrypoint"]
CMD ["--help"]
