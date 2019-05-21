CREATE EXTENSION "uuid-ossp";

CREATE TABLE urls (
    uuid uuid not null default uuid_generate_v4(),
    url text,
    name text,
    last_retrieved timestamp without time zone DEFAULT now(),
    primary key (uuid)
);

CREATE TABLE url_metadata (
    uuid uuid,
    url text,
    metadata jsonb,
    primary key (url)
);

CREATE TABLE content (
    uuid uuid not null default uuid_generate_v4(),
    url_uuid uuid,
    retrieved timestamp without time zone DEFAULT now(),
    data jsonb,
    cache_path text,
    primary key (uuid)
);

CREATE TABLE referers (
    url_uuid uuid NOT NULL,
    referer_uuid uuid NOT NULL,
    last_referred timestamp without time zone DEFAULT now()
);

CREATE TABLE dl_queue (
    uuid uuid not null default uuid_generate_v4(),
    url text,
    dl_order integer NOT NULL default 1000000,
    paused boolean NOT NULL default FALSE,
    paused_until timestamp,
    refresh_interval jsonb,
    primary key (uuid)
    added timestamp default now(),
);

CREATE TABLE active_dl (
    uuid uuid not null default uuid_generate_v4(),
    started_at timestamp default now(),
    started_by text,
    primary key (uuid)
);

CREATE TABLE pattern_wait (
    uuid uuid not null default uuid_generate_v4(),
    pattern text,
    wait int,
    primary key (uuid)
);

CREATE TABLE domain_wait (
    uuid uuid not null default uuid_generate_v4(),
    domain text unique,
    wait_until timestamp,
    primary key (uuid)
);
