FROM node:22-bookworm-slim

ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml tsconfig.base.json ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages/shared-types/package.json ./packages/shared-types/package.json
COPY packages/shared-ui/package.json ./packages/shared-ui/package.json
COPY packages/shared-worker-runtime/package.json ./packages/shared-worker-runtime/package.json

RUN pnpm install --frozen-lockfile=false

COPY apps ./apps
COPY packages ./packages

RUN pnpm --filter @epubdoctor/web build

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:3000').then((response)=>process.exit(response.ok?0:1)).catch(()=>process.exit(1))"

CMD ["pnpm", "--filter", "@epubdoctor/web", "start"]
