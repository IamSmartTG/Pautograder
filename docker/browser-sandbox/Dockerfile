FROM mcr.microsoft.com/playwright:v1.44.0-jammy

# Install the test runner OUTSIDE /submission — that path is bind-mounted with
# the student's files at grading time and would shadow a node_modules here.
# Pin to the image's browser version (1.44.0) to avoid a runner/browser mismatch.
WORKDIR /app
RUN npm init -y && npm install @playwright/test@1.44.0
ENV NODE_PATH=/app/node_modules
ENV PATH="/app/node_modules/.bin:${PATH}"

WORKDIR /submission
