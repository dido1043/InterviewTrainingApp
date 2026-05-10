FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy app source
COPY . .

EXPOSE 8081

# Start the development server
CMD ["npm", "start"]
