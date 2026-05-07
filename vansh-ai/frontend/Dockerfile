# Frontend Dockerfile for Vansh AI
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy remaining source
COPY . .

# Expose the port Next.js runs on (default 3000)
EXPOSE 3000

# Command to run the Next.js dev server
CMD ["npm", "run", "dev"]
