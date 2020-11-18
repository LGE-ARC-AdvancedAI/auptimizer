FROM nginx
COPY _build/html /usr/share/nginx/html

# fix version urls
RUN mkdir /usr/share/nginx/html/archive
RUN mv /usr/share/nginx/html/_static/*.whl /usr/share/nginx/html/archive
RUN mv /usr/share/nginx/html/_static/aup.py /usr/share/nginx/html/archive/