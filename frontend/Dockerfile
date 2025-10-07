# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Создаем директорию для SSL сертификатов
RUN mkdir -p /etc/nginx/ssl

# Copy built app to nginx
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configurations
COPY nginx-minimal.conf /etc/nginx/conf.d/default.conf
COPY nginx-main.conf /etc/nginx/nginx.conf

# Expose ports
EXPOSE 80 443

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
