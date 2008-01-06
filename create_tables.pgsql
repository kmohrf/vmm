-- $Id$ 

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
    domainname  varchar(255) NOT NULL,
    transport   varchar(268) NOT NULL DEFAULT 'dovecot:', -- smtp:[255-char.host.name:50025]
    domaindir   varchar(40) NOT NULL, --/srv/mail/$RAND/4294967294
    CONSTRAINT pkey_domains PRIMARY KEY (gid),
    CONSTRAINT ukey_domains UNIQUE (domainname)
);

CREATE TABLE users (
    local_part  varchar(64) NOT NULL,-- only localpart w/o '@'
    passwd      varchar(74) NOT NULL,-- {CRAM-MD5}+64hex numbers
    name        varchar(128) NULL,
    uid         bigint NOT NULL DEFAULT nextval('users_uid'),
    gid         bigint NOT NULL,
  --home        varchar(40) NOT NULL, --/home/virtualmail/4294967294/4294967294
    home        bigint NOT NULL, -- 4294967294
    mail        varchar(128) NOT NULL DEFAULT 'Maildir',
    disabled    boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pkye_users PRIMARY KEY (local_part, gid),
    CONSTRAINT ukey_users_uid UNIQUE (uid),
    CONSTRAINT fkey_users_gid_domains FOREIGN KEY (gid)
        REFERENCES domains (gid)
);

CREATE SEQUENCE alias_id;
CREATE TABLE alias (
    id          bigint NOT NULL DEFAULT nextval('alias_id'),
    gid         bigint NOT NULL,
    address     varchar(256) NOT NULL,
    destination varchar(320) NOT NULL,
    CONSTRAINT pkey_alias PRIMARY KEY (gid, address, destination),
    CONSTRAINT fkey_alias_gid_domains FOREIGN KEY (gid)
        REFERENCES domains (gid)
);

CREATE SEQUENCE relocated_id;
CREATE TABLE relocated (
    id          bigint NOT NULL DEFAULT nextval('relocated_id'),
    gid         bigint NOT NULL,
    address     varchar(64) NOT NULL,
    destination varchar(320) NOT NULL,
    CONSTRAINT pkey_relocated PRIMARY KEY (gid, address),
    CONSTRAINT fkey_relocated_gid_domains FOREIGN KEY (gid)
        REFERENCES domains (gid)
);

CREATE OR REPLACE VIEW dovecot_password AS
    SELECT local_part || '@' || domains.domainname AS user,
           passwd AS password
      FROM users
           LEFT JOIN domains USING (gid);

CREATE OR REPLACE VIEW dovecot_user AS
    SELECT local_part || '@' || domains.domainname AS userid,
           domains.domaindir || '/' || home AS home,
           uid,
           gid
      FROM users
           LEFT JOIN domains USING (gid);

CREATE OR REPLACE VIEW postfix_gid AS
    SELECT gid, domainname
      FROM domains;

CREATE OR REPLACE VIEW postfix_uid AS
    SELECT local_part || '@' || domains.domainname AS address,
           uid
      FROM users
           LEFT JOIN domains USING (gid);

CREATE OR REPLACE VIEW postfix_maildir AS
    SELECT local_part || '@' || domains.domainname AS address,
           domains.domaindir || '/' || home || '/' || mail || '/' AS maildir
      FROM users
           LEFT JOIN domains USING (gid);

CREATE OR REPLACE VIEW postfix_relocated AS
    SELECT address || '@' || domains.domainname AS address, destination
      FROM relocated
           LEFT JOIN domains USING (gid);

CREATE OR REPLACE VIEW postfix_alias AS
    SELECT address || '@' || domains.domainname AS address, destination, gid
      FROM alias
           LEFT JOIN domains USING (gid);

CREATE OR REPLACE VIEW postfix_transport AS
    SELECT transport, domainname
      FROM domains;

CREATE OR REPLACE VIEW vmm_alias_count AS
    SELECT count(DISTINCT address) AS aliases, gid
      FROM alias 
  GROUP BY gid;
