# The frontend is a static site (no bundler/build step -- see README for why:
# npm could not reach the registry in the build sandbox). This just serves
# the static files; any static server works equally well.
FROM python:3.12-slim
WORKDIR /site
COPY frontend/ .
EXPOSE 8080
CMD ["python", "-m", "http.server", "8080"]
