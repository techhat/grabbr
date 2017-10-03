CREATE TABLE content (
    id serial primary key,
    url_id integer,
    retrieved timestamp without time zone DEFAULT now(),
    data jsonb,
    cache_path text
);

CREATE TABLE dl_queue (
    id serial primary key,
    url text
);

CREATE TABLE referers (
    url_id integer NOT NULL,
    referer_id integer NOT NULL,
    last_referred timestamp without time zone DEFAULT now()
);

CREATE TABLE urls (
    id serial primary key,
    url text,
    last_retrieved timestamp without time zone DEFAULT now()
);
