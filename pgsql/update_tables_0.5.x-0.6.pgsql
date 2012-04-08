SET client_encoding = 'UTF8';
SET client_min_messages = warning;

-- ---
-- Create the new service_set table and insert all possible combinations
-- --
CREATE SEQUENCE service_set_id;

CREATE TABLE service_set (
    ssid        bigint NOT NULL DEFAULT nextval('service_set_id'),
    smtp        boolean NOT NULL DEFAULT TRUE,
    pop3        boolean NOT NULL DEFAULT TRUE,
    imap        boolean NOT NULL DEFAULT TRUE,
    managesieve boolean NOT NULL DEFAULT TRUE,
    CONSTRAINT  pkey_service_set PRIMARY KEY (ssid),
    CONSTRAINT  ukey_service_set UNIQUE (smtp, pop3, imap, managesieve)
);

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

-- ---
-- Drop the obsolete VIEWs, we've functions now.
-- ---
DROP VIEW dovecot_user;
DROP VIEW dovecot_password;
DROP VIEW postfix_alias;
DROP VIEW postfix_maildir;
DROP VIEW postfix_relocated;
DROP VIEW postfix_transport;
DROP VIEW postfix_uid;
-- the vmm_domain_info view will be restored later
DROP VIEW vmm_domain_info;

CREATE SEQUENCE mailboxformat_id;
CREATE SEQUENCE quotalimit_id;

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

-- Adjust maillocation table
ALTER TABLE maillocation DROP CONSTRAINT ukey_maillocation;
ALTER TABLE maillocation RENAME COLUMN maillocation TO directory;
ALTER TABLE maillocation
    ADD COLUMN fid bigint NOT NULL DEFAULT 1,
    ADD COLUMN extra varchar(1024);
ALTER TABLE maillocation ADD CONSTRAINT fkey_maillocation_fid_mailboxformat
    FOREIGN KEY (fid) REFERENCES mailboxformat (fid);

ALTER TABLE users ALTER COLUMN passwd TYPE varchar(270);

-- ---
-- Add quota stuff
-- ---
CREATE TABLE quotalimit (
    qid         bigint NOT NULL DEFAULT nextval('quotalimit_id'),
    bytes       bigint NOT NULL,
    messages    integer NOT NULL DEFAULT 0,
    CONSTRAINT  pkey_quotalimit PRIMARY KEY (qid),
    CONSTRAINT  ukey_quotalimit UNIQUE (bytes, messages)
);
-- Insert default (non) quota limit
INSERT INTO quotalimit(bytes, messages) VALUES (0, 0);

-- Adjust tables (quota)
ALTER TABLE domain_data ADD COLUMN qid bigint NOT NULL DEFAULT 1;
ALTER TABLE domain_data ADD CONSTRAINT fkey_domain_data_qid_quotalimit
    FOREIGN KEY (qid) REFERENCES quotalimit (qid);

ALTER TABLE users ADD COLUMN qid bigint NOT NULL DEFAULT 1;
ALTER TABLE users ADD CONSTRAINT fkey_users_qid_quotalimit
    FOREIGN KEY (qid) REFERENCES quotalimit (qid);

CREATE TABLE userquota_11 (
    uid         bigint NOT NULL,
    path        varchar(16) NOT NULL,
    current     bigint NOT NULL DEFAULT 0,
    CONSTRAINT  pkey_userquota_11 PRIMARY KEY (uid, path),
    CONSTRAINT  fkey_userquota_11_uid_users FOREIGN KEY (uid)
        REFERENCES users (uid) ON DELETE CASCADE
);

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

-- Adjust tables (services)
ALTER TABLE domain_data ADD COLUMN ssid bigint NOT NULL DEFAULT 1;
ALTER TABLE domain_data ADD CONSTRAINT fkey_domain_data_ssid_service_set
    FOREIGN KEY (ssid) REFERENCES service_set (ssid);

ALTER TABLE users ADD COLUMN ssid bigint NOT NULL DEFAULT 1;
-- save current service sets
UPDATE users u
   SET ssid = ss.ssid
  FROM service_set ss
 WHERE ss.smtp = u.smtp
   AND ss.pop3 = u.pop3
   AND ss.imap = u.imap
   AND ss.managesieve = u.managesieve;

ALTER TABLE users DROP COLUMN smtp;
ALTER TABLE users DROP COLUMN pop3;
ALTER TABLE users DROP COLUMN imap;
ALTER TABLE users DROP COLUMN managesieve;
ALTER TABLE users ADD CONSTRAINT fkey_users_ssid_service_set
    FOREIGN KEY (ssid) REFERENCES service_set (ssid);

-- ---
-- Restore view
-- ---
CREATE VIEW vmm_domain_info AS
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
