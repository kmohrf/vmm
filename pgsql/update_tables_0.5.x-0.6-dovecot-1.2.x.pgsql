SET client_encoding = 'UTF8';
SET client_min_messages = warning;


-- ---
-- Make room for sha512-crypt.hex hashed passwords
-- ---
DROP VIEW dovecot_password;

ALTER TABLE users ALTER COLUMN passwd TYPE varchar(270);

CREATE VIEW dovecot_password AS
    SELECT local_part || '@' || domain_name.domainname AS "user",
           passwd AS "password", smtp, pop3, imap, sieve
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

-- Adjust tables
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
        REFERENCES users (uid)
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
