SET client_encoding = 'UTF8';
SET client_min_messages = warning;


-- ---
-- Make room for sha512-crypt.hex hashed passwords
-- ---
DROP VIEW dovecot_password;

ALTER TABLE users ALTER COLUMN passwd TYPE varchar(270);

CREATE VIEW dovecot_password AS
    SELECT local_part || '@' || domain_name.domainname AS "user",
           passwd AS "password", smtp, pop3, imap, managesieve
      FROM users
           LEFT JOIN domain_name USING (gid);

-- ---
-- Make room for different mailbox formats.
-- ---
DROP VIEW dovecot_user;
DROP VIEW postfix_maildir;

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

-- Adjust tables …
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

CREATE VIEW postfix_maildir AS
    SELECT local_part || '@' || domain_name.domainname AS address,
           domain_data.domaindir||'/'||uid||'/'||maillocation.directory||'/'
           AS maildir
      FROM users
           LEFT JOIN domain_data USING (gid)
           LEFT JOIN domain_name USING (gid)
           LEFT JOIN maillocation USING (mid);
