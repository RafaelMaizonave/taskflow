FROM node:24-bookworm-slim AS development
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

FROM development AS e2e
RUN npx playwright install --with-deps chromium
CMD ["npm", "run", "test:e2e"]
