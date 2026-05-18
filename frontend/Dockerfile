FROM node:20-alpine
WORKDIR /app
COPY . .
RUN npm install
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=http://localhost:8000
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
EXPOSE 3000
CMD ["npx", "next", "dev", "-p", "3000"]
