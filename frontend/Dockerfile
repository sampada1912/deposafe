FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
COPY .browserslistrc ./
RUN npm ci

COPY . .

# Ensure public folder exists so runner COPY step never fails
RUN mkdir -p /app/public

# Support baking NEXT_PUBLIC_API_URL into the Next.js production build
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-http://localhost:8000/api/v1}

RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000

COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules

# Run container as non-root node user
USER node

EXPOSE 3000

CMD ["sh", "-c", "npx next start -p ${PORT:-3000}"]
