# Build stage
FROM node:20-alpine as build

WORKDIR /app

# Cache dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy source code
COPY . .

# Build React application
RUN npm run build

# Verify build directory
RUN ls -la /app/dist || echo "Dist directory contents:"
RUN find /app -name "index.html" | head -5

# Production stage
FROM nginx:alpine

# Copy build from dist (Vite default)
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]