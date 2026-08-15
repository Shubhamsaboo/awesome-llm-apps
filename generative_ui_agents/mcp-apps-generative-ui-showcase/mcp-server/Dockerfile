FROM node:20-slim

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source files
COPY . .

# Build TypeScript and app HTML
RUN npm run build

# Expose port
EXPOSE 3001

# Start server
CMD ["npm", "start"]
