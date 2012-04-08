SET client_encoding = 'UTF8';
SET client_min_messages = warning;


CREATE SEQUENCE transport_id;

CREATE SEQUENCE mailboxformat_id;

CREATE SEQUENCE quotalimit_id;

CREATE SEQUENCE maillocation_id;

CREATE SEQUENCE service_set_id;

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

CREATE TABLE mailboxformat (
    fid         bigint NOT NULL DEFAULT nextval('mailboxformat_id'),
    format      varchar(20) NOT NULL,
    CONSTRAINT  pkey_mailboxformat PRIMARY KEY (fid),
    CONSTRAINT  ukey_mailboxformat UNIQUE (format)
);
-- Insert supported mailbox formats
INSERT INTO mailboxformat(format) VALUES ('maildir');
INSERT INTO mailboxformat(format) VALUES ('mdbox');
INSERT INTO mailboxformat(format) VALUES ('sdbox');

CREATE TABLE maillocation (
    mid         bigint NOT NULL DEFAULT nextval('maillocation_id'),
    fid         bigint NOT NULL DEFAULT 1,
    directory   varchar(20) NOT NULL,
    extra       varchar(1024),
    CONSTRAINT  pkey_maillocation PRIMARY KEY (mid),
    CONSTRAINT  fkey_maillocation_fid_mailboxformat FOREIGN KEY (fid)
        REFERENCES mailboxformat (fid)
);
-- Insert default Maildir-folder name
INSERT INTO maillocation(directory) VALUES ('Maildir');

CREATE TABLE quotalimit (
    qid         bigint NOT NULL DEFAULT nextval('quotalimit_id'),
    bytes       bigint NOT NULL,
    messages    integer NOT NULL DEFAULT 0,
    CONSTRAINT  pkey_quotalimit PRIMARY KEY (qid),
    CONSTRAINT  ukey_quotalimit UNIQUE (bytes, messages)
);
-- Insert default (non) quota limit
INSERT INTO quotalimit(bytes, messages) VALUES (0, 0);

CREATE TABLE service_set (
    ssid        bigint NOT NULL DEFAULT nextval('service_set_id'),
    smtp        boolean NOT NULL DEFAULT TRUE,
    pop3        boolean NOT NULL DEFAULT TRUE,
    imap        boolean NOT NULL DEFAULT TRUE,
    managesieve boolean NOT NULL DEFAULT TRUE,
    CONSTRAINT  pkey_service_set PRIMARY KEY (ssid),
    CONSTRAINT  ukey_service_set UNIQUE (smtp, pop3, imap, managesieve)
);
-- Insert all possible service combinations
COPY service_set (smtp, pop3, imap, managesieve) FROM stdin;
TRUE	TRUE	TRUE	TRUE
FALSE	TRUE	TRUE	TRUE
TRUE	FALSE	TRUE	TRUE
FALSE	FALSE	TRUE	TRUE
TRUE	TRUE	FALSE	TRUE
FALSE	TRUE	FALSE	TRUE
TRUE	FALSE	FALSE	TRUE
FALSE	FALSE	FALSE	TRUE
TRUE	TRUE	TRUE	FALSE
FALSE	TRUE	TRUE	FALSE
TRUE	FALSE	TRUE	FALSE
FALSE	FALSE	TRUE	FALSE
TRUE	TRUE	FALSE	FALSE
FALSE	TRUE	FALSE	FALSE
TRUE	FALSE	FALSE	FALSE
FALSE	FALSE	FALSE	FALSE
\.

CREATE TABLE domain_data (
    gid         bigint NOT NULL DEFAULT nextval('domain_gid'),
    qid         bigint NOT NULL DEFAULT 1, -- default quota limit
    ssid        bigint NOT NULL DEFAULT 1, -- default service_set
    tid         bigint NOT NULL DEFAULT 1, -- default transport
    domaindir   varchar(40) NOT NULL, --/srv/mail/$RAND/4294967294
    CONSTRAINT  pkey_domain_data PRIMARY KEY (gid),
    CONSTRAINT  fkey_domain_data_qid_quotalimit FOREIGN KEY (qid)
        REFERENCES quotalimit (qid),
    CONSTRAINT  fkey_domain_data_ssid_service_set FOREIGN KEY (ssid)
        REFERENCES service_set (ssid),
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
    passwd      varchar(270) NOT NULL,
    name        varchar(128) NULL,
    uid         bigint NOT NULL DEFAULT nextval('users_uid'),
    gid         bigint NOT NULL,
    mid         bigint NOT NULL DEFAULT 1,
    qid         bigint NOT NULL DEFAULT 1,
    ssid        bigint NOT NULL DEFAULT 1,
    tid         bigint NOT NULL DEFAULT 1,
    CONSTRAINT  pkey_users PRIMARY KEY (local_part, gid),
    CONSTRAINT  ukey_users_uid UNIQUE (uid),
    CONSTRAINT  fkey_users_gid_domain_data FOREIGN KEY (gid)
        REFERENCES domain_data (gid),
    CONSTRAINT  fkey_users_mid_maillocation FOREIGN KEY (mid)
        REFERENCES maillocation (mid),
    CONSTRAINT  fkey_users_qid_quotalimit FOREIGN KEY (qid)
        REFERENCES quotalimit (qid),
    CONSTRAINT fkey_users_ssid_service_set FOREIGN KEY (ssid)
        REFERENCES service_set (ssid),
    CONSTRAINT  fkey_users_tid_transport FOREIGN KEY (tid)
        REFERENCES transport (tid)
);

CREATE TABLE userquota_11 (
    uid         bigint NOT NULL,
    path        varchar(16) NOT NULL,
    current     bigint NOT NULL DEFAULT 0,
    CONSTRAINT  pkey_userquota_11 PRIMARY KEY (uid, path),
    CONSTRAINT  fkey_userquota_11_uid_users FOREIGN KEY (uid)
        REFERENCES users (uid) ON DELETE CASCADE
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

CREATE OR REPLACE VIEW postfix_gid AS
    SELECT gid, domainname
      FROM domain_name;

CREATE OR REPLACE VIEW vmm_domain_info AS
    SELECT gid, count(uid) AS accounts,
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
           LEFT JOIN users USING (gid)
     WHERE domain_name.is_primary
  GROUP BY gid;


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


CREATE OR REPLACE FUNCTION merge_userquota_11() RETURNS TRIGGER AS $$
BEGIN
    UPDATE userquota_11
       SET current = current + NEW.current
     WHERE uid = NEW.uid AND path = NEW.path;
    IF found THEN
        RETURN NULL;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER mergeuserquota_11 BEFORE INSERT ON userquota_11
    FOR EACH ROW EXECUTE PROCEDURE merge_userquota_11();
