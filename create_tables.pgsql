-- $Id$ 

SET client_encoding = 'UTF8';
SET client_min_messages = warning;


CREATE SEQUENCE transport_id;

CREATE SEQUENCE maillocation_id;

CREATE SEQUENCE domain_gid
    START WITH 70000
    INCREMENT BY 1
    MINVALUE 70000
    MAXVALUE 4294967294
    NO CYCLE;

CREATE SEQUENCE users_uid
    START WITH 70000
    INCREMENT BY 1
    MINVALUE 70000
    MAXVALUE 4294967294
    NO CYCLE;


CREATE TABLE transport (
    tid         bigint NOT NULL DEFAULT nextval('transport_id'),
    transport   varchar(270) NOT NULL, -- smtps:[255-char.host.name:50025]
    CONSTRAINT  pkey_transport PRIMARY KEY (tid),
    CONSTRAINT  ukey_transport UNIQUE (transport)
);
-- Insert default transport
INSERT INTO transport(transport) VALUES ('dovecot:');

CREATE TABLE maillocation(
    mid     bigint NOT NULL DEFAULT nextval('maillocation_id'),
    maillocation varchar(20) NOT NULL,
    CONSTRAINT  pkey_maillocation PRIMARY KEY (mid),
    CONSTRAINT  ukey_maillocation UNIQUE (maillocation)
);
-- Insert default Maildir-folder name
INSERT INTO maillocation(maillocation) VALUES ('Maildir');

CREATE TABLE domain_data (
    gid         bigint NOT NULL DEFAULT nextval('domain_gid'),
    tid         bigint NOT NULL DEFAULT 1, -- defualt transport
    domaindir   varchar(40) NOT NULL, --/srv/mail/$RAND/4294967294
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

CREATE TABLE users (
    local_part  varchar(64) NOT NULL,-- only localpart w/o '@'
    passwd      varchar(74) NOT NULL,-- {CRAM-MD5}+64hex numbers
    name        varchar(128) NULL,
    uid         bigint NOT NULL DEFAULT nextval('users_uid'),
    gid         bigint NOT NULL,
    mid         bigint NOT NULL DEFAULT 1,
    tid         bigint NOT NULL DEFAULT 1,
    smtp        boolean NOT NULL DEFAULT TRUE,
    pop3        boolean NOT NULL DEFAULT TRUE,
    imap        boolean NOT NULL DEFAULT TRUE,
    managesieve boolean NOT NULL DEFAULT TRUE,
    CONSTRAINT  pkye_users PRIMARY KEY (local_part, gid),
    CONSTRAINT  ukey_users_uid UNIQUE (uid),
    CONSTRAINT  fkey_users_gid_domain_data FOREIGN KEY (gid)
        REFERENCES domain_data (gid),
    CONSTRAINT  fkey_users_mid_maillocation FOREIGN KEY (mid)
        REFERENCES maillocation (mid),
    CONSTRAINT  fkey_users_tid_transport FOREIGN KEY (tid)
        REFERENCES transport (tid)
);

CREATE TABLE alias (
    gid         bigint NOT NULL,
    address     varchar(64) NOT NULL,-- only localpart w/o '@'
    destination varchar(320) NOT NULL,
    CONSTRAINT  pkey_alias PRIMARY KEY (gid, address, destination),
    CONSTRAINT  fkey_alias_gid_domain_data FOREIGN KEY (gid)
        REFERENCES domain_data (gid)
);

CREATE TABLE relocated (
    gid         bigint NOT NULL,
    address     varchar(64) NOT NULL,
    destination varchar(320) NOT NULL,
    CONSTRAINT  pkey_relocated PRIMARY KEY (gid, address),
    CONSTRAINT  fkey_relocated_gid_domain_data FOREIGN KEY (gid)
        REFERENCES domain_data (gid)
);

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

CREATE OR REPLACE VIEW vmm_alias_count AS
    SELECT count(DISTINCT address) AS aliases, gid
      FROM alias 
  GROUP BY gid;

CREATE OR REPLACE VIEW vmm_domain_info AS
    SELECT gid, domainname, transport, domaindir,
           count(uid) AS accounts,
           aliases,
           (SELECT count(gid)
              FROM domain_name
             WHERE domain_name.gid = domain_data.gid
               AND NOT domain_name.is_primary) AS aliasdomains
      FROM domain_data
           LEFT JOIN domain_name USING (gid)
           LEFT JOIN transport USING (tid)
           LEFT JOIN users USING (gid)
           LEFT JOIN vmm_alias_count USING (gid)
     WHERE domain_name.is_primary
  GROUP BY gid, domainname, transport, domaindir, aliases;


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
