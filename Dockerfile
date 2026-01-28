# syntax=docker/dockerfile:1

# =============================================================================
# Stage 1: Builder - uv로 의존성 설치
# =============================================================================
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

# 버전 정보 (hatch-vcs용 - .git 없이 빌드 지원)
ARG VERSION=0.0.0
ENV SETUPTOOLS_SCM_PRETEND_VERSION=${VERSION}

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# 의존성 먼저 설치 (레이어 캐싱 최적화)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev --all-extras

# 소스 코드 복사 및 프로젝트 설치
COPY src/ /app/src/
COPY pyproject.toml uv.lock README.md LICENSE /app/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --all-extras --no-editable

# =============================================================================
# Stage 2: Runtime - 최소 프로덕션 이미지
# =============================================================================
FROM python:3.14-slim-bookworm AS runtime

# 보안: non-root 사용자
RUN groupadd --gid 1000 chzzk && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home chzzk

# 가상환경만 복사
COPY --from=builder --chown=chzzk:chzzk /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER chzzk
WORKDIR /home/chzzk

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD chzzk --help || exit 1

ENTRYPOINT ["chzzk"]
CMD ["--help"]
