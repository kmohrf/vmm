-- $Id$ 

CREATE SEQUENCE transport_id;
CREATE TABLE transport (
    tid         bigint NOT NULL DEFAULT nextval('transport_id'),
    transport   varchar(270) NOT NULL, -- smtps:[255-char.host.name:50025]
    CONSTRAINT pkey_transport PRIMARY KEY (tid),
    CONSTRAINT ukey_transport UNIQUE (transport)
);
-- Insert default transport
INSERT INTO transport(transport) VALUES ('dovecot:');

CREATE SEQUENCE maillocation_id;
CREATE TABLE maillocation(
    mid     bigint NOT NULL DEFAULT nextval('maillocation_id'),
    maillocation varchar(20) NOT NULL,
    CONSTRAINT pkey_maillocation PRIMARY KEY (mid),
    CONSTRAINT ukey_maillocation UNIQUE (maillocation)
);
-- Insert default Maildir-folder name
INSERT INTO maillocation(maillocation) VALUES ('Maildir');

CREATE SEQUENCE domains_gid
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

CREATE TABLE domains (
    gid         bigint NOT NULL DEFAULT nextval('domains_gid'),
    tid         bigint NOT NULL DEFAULT 1, -- defualt transport
    domainname  varchar(255) NOT NULL,
    domaindir   varchar(40) NOT NULL, --/srv/mail/$RAND/4294967294
    CONSTRAINT pkey_domains PRIMARY KEY (gid),
    CONSTRAINT ukey_domains UNIQUE (domainname),
    CONSTRAINT fkey_domains_tid_transport FOREIGN KEY (tid)
        REFERENCES transport (tid)
);

CREATE TABLE users (
    local_part  varchar(64) NOT NULL,-- only localpart w/o '@'
    passwd      varchar(74) NOT NULL,-- {CRAM-MD5}+64hex numbers
    name        varchar(128) NULL,
    uid         bigint NOT NULL DEFAULT nextval('users_uid'),
    gid         bigint NOT NULL,
    mid         bigint NOT NULL DEFAULT 1,
    tid         bigint NOT NULL DEFAULT 1,
    smpt        boolean NOT NULL DEFAULT TRUE,
    pop3        boolean NOT NULL DEFAULT TRUE,
    imap        boolean NOT NULL DEFAULT TRUE,
    managesieve boolean NOT NULL DEFAULT TRUE,
    CONSTRAINT pkye_users PRIMARY KEY (local_part, gid),
    CONSTRAINT ukey_users_uid UNIQUE (uid),
    CONSTRAINT fkey_users_gid_domains FOREIGN KEY (gid)
        REFERENCES domains (gid),
    CONSTRAINT fkey_users_mid_maillocation FOREIGN KEY (mid)
        REFERENCES maillocation (mid),
    CONSTRAINT fkey_users_tid_transport FOREIGN KEY (tid)
        REFERENCES transport (tid)
);

CREATE TABLE alias (
    gid         bigint NOT NULL,
    address     varchar(256) NOT NULL,
    destination varchar(320) NOT NULL,
    CONSTRAINT pkey_alias PRIMARY KEY (gid, address, destination),
    CONSTRAINT fkey_alias_gid_domains FOREIGN KEY (gid)
        REFERENCES domains (gid)
);

CREATE TABLE relocated (
    gid         bigint NOT NULL,
    address     varchar(64) NOT NULL,
    destination varchar(320) NOT NULL,
    CONSTRAINT pkey_relocated PRIMARY KEY (gid, address),
    CONSTRAINT fkey_relocated_gid_domains FOREIGN KEY (gid)
        REFERENCES domains (gid)
);

CREATE OR REPLACE VIEW dovecot_password AS
    SELECT local_part || '@' || domains.domainname AS "user",
           passwd AS "password", smtp, pop3, imap, managesieve
      FROM users
           LEFT JOIN domains USING (gid);

CREATE OR REPLACE VIEW dovecot_user AS
    SELECT local_part || '@' || domains.domainname AS userid,
           uid, gid, domains.domaindir || '/' || uid AS home,
           '~/' || maillocation.maillocation AS mail
      FROM users
           LEFT JOIN domains USING (gid)
           LEFT JOIN maillocation USING (mid);

CREATE OR REPLACE VIEW postfix_gid AS
    SELECT gid, domainname
      FROM domains;

CREATE OR REPLACE VIEW postfix_uid AS
    SELECT local_part || '@' || domains.domainname AS address, uid
      FROM users
           LEFT JOIN domains USING (gid);

CREATE OR REPLACE VIEW postfix_maildir AS
    SELECT local_part || '@' || domains.domainname AS address,
           domains.domaindir||'/'||uid||'/'||maillocation.maillocation||'/' AS maildir
      FROM users
           LEFT JOIN domains USING (gid)
           LEFT JOIN maillocation USING (mid);

CREATE OR REPLACE VIEW postfix_relocated AS
    SELECT address || '@' || domains.domainname AS address, destination
      FROM relocated
           LEFT JOIN domains USING (gid);

CREATE OR REPLACE VIEW postfix_alias AS
    SELECT address || '@' || domains.domainname AS address, destination, gid
      FROM alias
           LEFT JOIN domains USING (gid);

CREATE OR REPLACE VIEW postfix_transport AS
    SELECT local_part || '@' || domains.domainname AS address,
           transport.transport
      FROM users
           LEFT JOIN transport USING (tid)
           LEFT JOIN domains USING (gid);

CREATE OR REPLACE VIEW vmm_alias_count AS
    SELECT count(DISTINCT address) AS aliases, gid
      FROM alias 
  GROUP BY gid;

CREATE OR REPLACE VIEW vmm_domain_info AS
    SELECT gid, domainname, transport, domaindir, count(uid) AS accounts,
           aliases
      FROM domains
           LEFT JOIN transport USING (tid)
           LEFT JOIN users USING (gid)
           LEFT JOIN vmm_alias_count USING (gid)
  GROUP BY gid, domainname, transport, domaindir, aliases;
