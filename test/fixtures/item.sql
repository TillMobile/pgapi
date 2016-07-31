create extension hstore;

create table item (
  id serial primary key,
  name varchar,
  description varchar,
  attributes hstore
 );

create table supported_types (
  a smallint primary key,
  b integer,
  c bigint,
  d decimal,
  e numeric,
  f real,
  g double precision,
  h smallserial,
  i serial,
  j bigserial,
  k money,
  l bytea,
  m boolean,
  n varchar(10),
  o char(1),
  p text,
  q timestamp without time zone,
  r timestamp with time zone,
  s date,
  t time without time zone,
  u time with time zone,
  v jsonb,
  w hstore
);

create function items_by_size(t_size varchar)
returns setof item as $$
  select * from item where attributes->'size' = t_size;
$$ language 'sql';