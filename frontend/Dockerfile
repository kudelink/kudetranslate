FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .
RUN npm run build

FROM node:20-alpine

WORKDIR /app

# Copy package files and install all dependencies (including production)
COPY --from=builder /app/package.json ./
RUN npm install

# Copy server.js and dist
COPY --from=builder /app/server.js ./
COPY --from=builder /app/dist ./dist

EXPOSE 80

CMD ["node", "server.js"]
