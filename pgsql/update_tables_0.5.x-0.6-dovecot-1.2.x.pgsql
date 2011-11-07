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
    sieve       boolean NOT NULL DEFAULT TRUE,
    CONSTRAINT  pkey_service_set PRIMARY KEY (ssid),
    CONSTRAINT  ukey_service_set UNIQUE (smtp, pop3, imap, sieve)
);

COPY service_set (smtp, pop3, imap, sieve) FROM stdin;
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
-- Make room for different mailbox formats and longer password hashes.
-- ---
DROP VIEW dovecot_user;
DROP VIEW dovecot_password;
DROP VIEW postfix_maildir;
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

CREATE TABLE userquota (
    uid         bigint NOT NULL,
    bytes       bigint NOT NULL DEFAULT 0,
    messages    integer NOT NULL DEFAULT 0,
    CONSTRAINT  pkey_userquota PRIMARY KEY (uid),
    CONSTRAINT  fkey_userquota_uid_users FOREIGN KEY (uid)
        REFERENCES users (uid) ON DELETE CASCADE
);

CREATE OR REPLACE FUNCTION merge_userquota() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.messages < 0 OR NEW.messages IS NULL THEN
        IF NEW.messages IS NULL THEN
            NEW.messages = 0;
        ELSE
            NEW.messages = -NEW.messages;
        END IF;
        RETURN NEW;
    END IF;
    LOOP
        UPDATE userquota
           SET bytes = bytes + NEW.bytes, messages = messages + NEW.messages
         WHERE uid = NEW.uid;
        IF found THEN
            RETURN NULL;
        END IF;
        BEGIN
            IF NEW.messages = 0 THEN
              INSERT INTO userquota VALUES (NEW.uid, NEW.bytes, NULL);
            ELSE
              INSERT INTO userquota VALUES (NEW.uid, NEW.bytes, -NEW.messages);
            END IF;
            RETURN NULL;
        EXCEPTION
            WHEN unique_violation THEN
                -- do nothing, and loop to try the UPDATE again
            WHEN foreign_key_violation THEN
                -- break the loop: a non matching uid means no such user
                RETURN NULL;
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER mergeuserquota BEFORE INSERT ON userquota
    FOR EACH ROW EXECUTE PROCEDURE merge_userquota();

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
   AND ss.sieve = u.sieve;

ALTER TABLE users DROP COLUMN smtp;
ALTER TABLE users DROP COLUMN pop3;
ALTER TABLE users DROP COLUMN imap;
ALTER TABLE users DROP COLUMN sieve;
ALTER TABLE users ADD CONSTRAINT fkey_users_ssid_service_set
    FOREIGN KEY (ssid) REFERENCES service_set (ssid);

-- ---
-- Restore views
-- ---
CREATE VIEW dovecot_user AS
    SELECT local_part || '@' || domain_name.domainname AS userid,
           uid, gid, domain_data.domaindir || '/' || uid AS home,
           mailboxformat.format || ':~/' || maillocation.directory AS mail
      FROM users
           LEFT JOIN domain_data USING (gid)
           LEFT JOIN domain_name USING (gid)
           LEFT JOIN maillocation USING (mid)
           LEFT JOIN mailboxformat USING (fid);

CREATE OR REPLACE VIEW dovecot_password AS
    SELECT local_part || '@' || domainname AS "user",
           passwd AS "password", smtp, pop3, imap, sieve
      FROM users
           LEFT JOIN domain_name USING (gid)
           LEFT JOIN service_set USING (ssid);

CREATE VIEW postfix_maildir AS
    SELECT local_part || '@' || domain_name.domainname AS address,
           domain_data.domaindir||'/'||uid||'/'||maillocation.directory||'/'
           AS maildir
      FROM users
           LEFT JOIN domain_data USING (gid)
           LEFT JOIN domain_name USING (gid)
           LEFT JOIN maillocation USING (mid);

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
