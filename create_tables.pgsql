-- $Id$ 

CREATE SEQUENCE transport_id;
CREATE TABLE transport (
    tid         bigint NOT NULL DEFAULT nextval('transport_id'),
    transport   varchar(268) NOT NULL, -- smtp:[255-char.host.name:50025]
    CONSTRAINT pkey_transport PRIMARY KEY (tid),
    CONSTRAINT ukey_transport UNIQUE (transport)
);
-- Insert default transport
INSERT INTO transport(transport) VALUES ('dovecot:');

CREATE SEQUENCE maildir_id;
CREATE TABLE maildir(
    mid     bigint NOT NULL DEFAULT nextval('maildir_id'),
    maildir varchar(20) NOT NULL,
    CONSTRAINT pkey_maildir PRIMARY KEY (mid),
    CONSTRAINT ukey_maildir UNIQUE (maildir)
);
-- Insert default Maildir-folder name
INSERT INTO maildir(maildir) VALUES ('Maildir');

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
    mid         bigint NOT NULL DEFAULT 1,
    tid         bigint NOT NULL DEFAULT 1,
    disabled    boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pkye_users PRIMARY KEY (local_part, gid),
    CONSTRAINT ukey_users_uid UNIQUE (uid),
    CONSTRAINT fkey_users_gid_domains FOREIGN KEY (gid)
        REFERENCES domains (gid),
    CONSTRAINT fkey_users_mid_maildir FOREIGN KEY (mid)
        REFERENCES maildir (mid),
    CONSTRAINT fkey_users_tid_transport FOREIGN KEY (tid)
        REFERENCES transport (tid)
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
    SELECT local_part || '@' || domains.domainname AS "user",
           passwd AS "password"
      FROM users
           LEFT JOIN domains USING (gid);

CREATE OR REPLACE VIEW dovecot_user AS
    SELECT local_part || '@' || domains.domainname AS userid,
           domains.domaindir || '/' || uid AS home,
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
           domains.domaindir||'/'||uid||'/'||maildir.maildir||'/' AS maildir
      FROM users
           LEFT JOIN domains USING (gid)
           LEFT JOIN maildir USING (mid);

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
