-- $Id$ 

SET client_encoding = 'UTF8';
SET client_min_messages = warning;

ALTER SEQUENCE domains_gid RENAME TO domain_gid;


CREATE TABLE domain_data (
    gid         bigint NOT NULL DEFAULT nextval('domain_gid'),
    tid         bigint NOT NULL DEFAULT 1,
    domaindir   varchar(40) NOT NULL,
    CONSTRAINT  pkey_domain_data PRIMARY KEY (gid),
    CONSTRAINT  fkey_domain_data_tid_transport FOREIGN KEY (tid)
        REFERENCES transport (tid)
);

CREATE TABLE domain_name (
    domainname  varchar(255) NOT NULL,
    gid         bigint NOT NULL,
    is_primary  boolean NOT NULL,
    CONSTRAINT  pkey_domain_name PRIMARY KEY (domainname),
    CONSTRAINT  fkey_domain_name_gid_domain_data FOREIGN KEY (gid)
        REFERENCES domain_data (gid)
);

INSERT INTO domain_data (gid, tid, domaindir) 
    SELECT gid, tid, domaindir
      FROM domains;

INSERT INTO domain_name (domainname, gid, is_primary) 
    SELECT domainname, gid, TRUE
      FROM domains;


ALTER TABLE users DROP CONSTRAINT pkye_users;
ALTER TABLE users ADD CONSTRAINT  pkey_users PRIMARY KEY (local_part, gid);
ALTER TABLE users DROP CONSTRAINT fkey_users_gid_domains;
ALTER TABLE users ADD CONSTRAINT fkey_users_gid_domain_data FOREIGN KEY (gid)
    REFERENCES domain_data (gid);

ALTER TABLE alias DROP CONSTRAINT fkey_alias_gid_domains;
ALTER TABLE alias DROP CONSTRAINT pkey_alias;
ALTER TABLE alias ADD CONSTRAINT fkey_alias_gid_domain_data FOREIGN KEY (gid)
    REFERENCES domain_data (gid);

ALTER TABLE relocated DROP CONSTRAINT fkey_relocated_gid_domains;
ALTER TABLE relocated ADD CONSTRAINT fkey_relocated_gid_domain_data
    FOREIGN KEY (gid) REFERENCES domain_data (gid);


CREATE OR REPLACE VIEW dovecot_password AS
    SELECT local_part || '@' || domain_name.domainname AS "user",
           passwd AS "password", smtp, pop3, imap, managesieve
      FROM users
           LEFT JOIN domain_name USING (gid);

CREATE OR REPLACE VIEW dovecot_user AS
    SELECT local_part || '@' || domain_name.domainname AS userid,
           uid, gid, domain_data.domaindir || '/' || uid AS home,
           '~/' || maillocation.maillocation AS mail
      FROM users
           LEFT JOIN domain_data USING (gid)
           LEFT JOIN domain_name USING (gid)
           LEFT JOIN maillocation USING (mid);

CREATE OR REPLACE VIEW postfix_gid AS
    SELECT gid, domainname
      FROM domain_name;

CREATE OR REPLACE VIEW postfix_uid AS
    SELECT local_part || '@' || domain_name.domainname AS address, uid
      FROM users
           LEFT JOIN domain_name USING (gid);

CREATE OR REPLACE VIEW postfix_maildir AS
    SELECT local_part || '@' || domain_name.domainname AS address,
           domain_data.domaindir||'/'||uid||'/'||maillocation.maillocation||'/'
           AS maildir
      FROM users
           LEFT JOIN domain_data USING (gid)
           LEFT JOIN domain_name USING (gid)
           LEFT JOIN maillocation USING (mid);

CREATE OR REPLACE VIEW postfix_relocated AS
    SELECT address || '@' || domain_name.domainname AS address, destination
      FROM relocated
           LEFT JOIN domain_name USING (gid);

DROP VIEW postfix_alias;
DROP VIEW vmm_domain_info;
DROP VIEW vmm_alias_count;

ALTER TABLE alias ALTER address TYPE varchar(64);
ALTER TABLE alias ADD CONSTRAINT pkey_alias 
    PRIMARY KEY (gid, address, destination);

CREATE OR REPLACE VIEW postfix_alias AS
    SELECT address || '@' || domain_name.domainname AS address, destination, gid
      FROM alias
           LEFT JOIN domain_name USING (gid);

CREATE OR REPLACE VIEW postfix_transport AS
    SELECT local_part || '@' || domain_name.domainname AS address,
           transport.transport
      FROM users
           LEFT JOIN transport USING (tid)
           LEFT JOIN domain_name USING (gid);

CREATE OR REPLACE VIEW vmm_domain_info AS
    SELECT gid, domainname, transport, domaindir,
           count(uid) AS accounts,
           (SELECT count(DISTINCT address)
              FROM alias
             WHERE alias.gid = domain_data.gid) AS aliases,
           (SELECT count(gid)
              FROM relocated
             WHERE relocated.gid = domain_data.gid) AS relocated,
           (SELECT count(gid)
              FROM domain_name
             WHERE domain_name.gid = domain_data.gid
               AND NOT domain_name.is_primary) AS aliasdomains
      FROM domain_data
           LEFT JOIN domain_name USING (gid)
           LEFT JOIN transport USING (tid)
           LEFT JOIN users USING (gid)
     WHERE domain_name.is_primary
  GROUP BY gid, domainname, transport, domaindir;


DROP TABLE domains;


CREATE LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION domain_primary_trigger() RETURNS TRIGGER AS $$
DECLARE
    primary_count bigint;
BEGIN
    SELECT INTO primary_count count(gid) + NEW.is_primary::integer
      FROM domain_name
     WHERE domain_name.gid = NEW.gid
       AND is_primary;

    IF (primary_count > 1) THEN
        RAISE EXCEPTION 'There can only be one domain marked as primary.';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql STABLE;

CREATE TRIGGER primary_count_ins BEFORE INSERT ON domain_name
    FOR EACH ROW EXECUTE PROCEDURE domain_primary_trigger();

CREATE TRIGGER primary_count_upd AFTER UPDATE ON domain_name
    FOR EACH ROW EXECUTE PROCEDURE domain_primary_trigger();
