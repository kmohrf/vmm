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
-- Catchall
-- ---

CREATE TABLE catchall (
    gid         bigint NOT NULL,
    destination varchar(320) NOT NULL,
    CONSTRAINT  pkey_catchall PRIMARY KEY (gid, destination),
    CONSTRAINT  fkey_catchall_gid_domain_data FOREIGN KEY (gid)
        REFERENCES domain_data (gid)
);

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

-- ---
-- Drop all known v0.5 types (the dirty way)
-- ---
DROP TYPE address_maildir CASCADE;
DROP TYPE dovecotpassword CASCADE;
DROP TYPE dovecotuser CASCADE;
DROP TYPE recipient_destination CASCADE;
DROP TYPE recipient_transport CASCADE;
DROP TYPE recipient_uid CASCADE;
DROP TYPE sender_login CASCADE;

-- ######################## TYPEs ########################################### --

-- ---
-- Data type for function postfix_virtual_mailbox(varchar, varchar)
-- ---
CREATE TYPE address_maildir AS (
    address varchar(320),
    maildir text
);
-- ---
-- Data type for function dovecotpassword(varchar, varchar)
-- ---
CREATE TYPE dovecotpassword AS (
    userid      varchar(320),
    password    varchar(270),
    smtp        boolean,
    pop3        boolean,
    imap        boolean,
    managesieve boolean
);
-- ---
-- Data type for function dovecotquotauser(varchar, varchar)
-- ---
CREATE TYPE dovecotquotauser AS (
    userid      varchar(320),
    uid         bigint,
    gid         bigint,
    home        text,
    mail        text,
    quota_rule  text
);
-- ---
-- Data type for function dovecotuser(varchar, varchar)
-- ---
CREATE TYPE dovecotuser AS (
    userid      varchar(320),
    uid         bigint,
    gid         bigint,
    home        text,
    mail        text
);
-- ---
-- Data type for functions: postfix_relocated_map(varchar, varchar)
--                          postfix_virtual_alias_map(varchar, varchar)
-- ---
CREATE TYPE recipient_destination AS (
    recipient   varchar(320),
    destination text
);
-- ---
-- Data type for function postfix_transport_map(varchar, varchar)
-- ---
CREATE TYPE recipient_transport AS (
    recipient   varchar(320),
    transport   text
);
-- ---
-- Data type for function postfix_virtual_uid_map(varchar, varchar)
-- ---
CREATE TYPE recipient_uid AS (
    recipient   varchar(320),
    uid         bigint
);
-- ---
-- Data type for function postfix_smtpd_sender_login_map(varchar, varchar)
-- ---
CREATE TYPE sender_login AS (
    sender  varchar(320),
    login   text
);

-- ######################## FUNCTIONs ####################################### --

-- ---
-- Parameters (from login name [localpart@the_domain]):
--      varchar localpart
--      varchar the_domain
-- Returns: dovecotpassword records
-- ---
CREATE OR REPLACE FUNCTION dovecotpassword(
    IN localpart varchar, IN the_domain varchar) RETURNS SETOF dovecotpassword
AS $$
    DECLARE
        record dovecotpassword;
        userid varchar(320) := localpart || '@' || the_domain;
    BEGIN
        FOR record IN
            SELECT userid, passwd, smtp, pop3, imap, managesieve
              FROM users, service_set
             WHERE gid = (SELECT gid
                            FROM domain_name
                           WHERE domainname = the_domain)
               AND local_part = localpart
               AND service_set.ssid = users.ssid
            LOOP
                RETURN NEXT record;
            END LOOP;
        RETURN;
    END;
$$ LANGUAGE plpgsql STABLE
RETURNS NULL ON NULL INPUT
EXTERNAL SECURITY INVOKER;
-- ---
-- Nearly the same as function dovecotuser below. It returns additionally the
-- field quota_rule.
-- ---
CREATE OR REPLACE FUNCTION dovecotquotauser(
    IN localpart varchar, IN the_domain varchar) RETURNS SETOF dovecotquotauser
AS $$
    DECLARE
        record dovecotquotauser;
        userid varchar(320) := localpart || '@' || the_domain;
        did bigint := (SELECT gid FROM domain_name WHERE domainname=the_domain);
    BEGIN
        FOR record IN
            SELECT userid, uid, did, domaindir || '/' || uid AS home,
                   format || ':~/' || directory AS mail, '*:bytes=' ||
                   bytes || ':messages=' || messages AS quota_rule
              FROM users, domain_data, mailboxformat, maillocation, quotalimit
             WHERE users.gid = did
               AND users.local_part = localpart
               AND maillocation.mid = users.mid
               AND mailboxformat.fid = maillocation.fid
               AND domain_data.gid = did
               AND quotalimit.qid = users.qid
            LOOP
                RETURN NEXT record;
            END LOOP;
        RETURN;
    END;
$$ LANGUAGE plpgsql STABLE
RETURNS NULL ON NULL INPUT
EXTERNAL SECURITY INVOKER;
-- ---
-- Parameters (from login name [localpart@the_domain]):
--      varchar localpart
--      varchar the_domain
-- Returns: dovecotuser records
-- ---
CREATE OR REPLACE FUNCTION dovecotuser(
    IN localpart varchar, IN the_domain varchar) RETURNS SETOF dovecotuser
AS $$
    DECLARE
        record dovecotuser;
        userid varchar(320) := localpart || '@' || the_domain;
        did bigint := (SELECT gid FROM domain_name WHERE domainname=the_domain);
    BEGIN
        FOR record IN
            SELECT userid, uid, did, domaindir || '/' || uid AS home,
                   format || ':~/' || directory AS mail
              FROM users, domain_data, mailboxformat, maillocation
             WHERE users.gid = did
               AND users.local_part = localpart
               AND maillocation.mid = users.mid
               AND mailboxformat.fid = maillocation.fid
               AND domain_data.gid = did
            LOOP
                RETURN NEXT record;
            END LOOP;
        RETURN;
    END;
$$ LANGUAGE plpgsql STABLE
RETURNS NULL ON NULL INPUT
EXTERNAL SECURITY INVOKER;
-- ---
-- Parameters (from recipients address (MAIL TO) [localpart@the_domain]):
--      varchar localpart
--      varchar the_domain
-- Returns: recipient_destination records
-- ---
CREATE OR REPLACE FUNCTION postfix_relocated_map(
    IN localpart varchar, IN the_domain varchar)
    RETURNS SETOF recipient_destination
AS $$
    DECLARE
        record recipient_destination;
        recipient varchar(320) := localpart || '@' || the_domain;
        did bigint := (SELECT gid FROM domain_name WHERE domainname=the_domain);
    BEGIN
        FOR record IN
            SELECT recipient, destination
              FROM relocated
             WHERE gid = did
               AND address = localpart
            LOOP
                RETURN NEXT record;
            END LOOP;
        RETURN;
    END;
$$ LANGUAGE plpgsql STABLE
RETURNS NULL ON NULL INPUT
EXTERNAL SECURITY INVOKER;
-- ---
-- Parameters (from _sender_ address (MAIL FROM) [localpart@the_domain]):
--      varchar localpart
--      varchar the_domain
-- Returns: SASL _login_ names that own _sender_ addresses (MAIL FROM):
--      set of sender_login records.
-- ---
CREATE OR REPLACE FUNCTION postfix_smtpd_sender_login_map(
    IN localpart varchar, IN the_domain varchar) RETURNS SETOF sender_login
AS $$
    DECLARE
        rec sender_login;
        did bigint := (SELECT gid FROM domain_name WHERE domainname=the_domain);
        sender varchar(320) := localpart || '@' || the_domain;
    BEGIN
        -- Get all addresses for 'localpart' in the primary and aliased domains
        FOR rec IN
            SELECT sender, local_part || '@' || domainname
              FROM domain_name, users
             WHERE domain_name.gid = did
               AND users.gid = did
               AND users.local_part = localpart
            LOOP
                RETURN NEXT rec;
            END LOOP;
        IF NOT FOUND THEN
            -- Loop over the alias addresses for localpart@the_domain
            FOR rec IN
                SELECT DISTINCT sender, destination
                  FROM alias
                 WHERE alias.gid = did
                   AND alias.address = localpart
                LOOP
                    RETURN NEXT rec;
                END LOOP;
        END IF;
        RETURN;
    END;
$$ LANGUAGE plpgsql STABLE
RETURNS NULL ON NULL INPUT
EXTERNAL SECURITY INVOKER;
-- ---
-- Parameters (from recipients address (MAIL TO) [localpart@the_domain]):
--      varchar localpart
--      varchar the_domain
-- Returns: recipient_transport records
-- ---
CREATE OR REPLACE FUNCTION postfix_transport_map(
    IN localpart varchar, IN the_domain varchar)
    RETURNS SETOF recipient_transport
AS $$
    DECLARE
        record recipient_transport;
        recipient varchar(320) := localpart || '@' || the_domain;
    BEGIN
        FOR record IN
            SELECT recipient, transport
              FROM transport
             WHERE tid = (SELECT tid
                            FROM users
                           WHERE gid = (SELECT gid
                                          FROM domain_name
                                         WHERE domainname = the_domain)
                             AND local_part = localpart)
            LOOP
                RETURN NEXT record;
            END LOOP;
        RETURN;
    END;
$$ LANGUAGE plpgsql STABLE
RETURNS NULL ON NULL INPUT
EXTERNAL SECURITY INVOKER;
-- ---
-- Parameters (from recipients address (MAIL TO) [localpart@the_domain]):
--      varchar localpart
--      varchar the_domain
-- Returns: recipient_destination records
-- ---
CREATE OR REPLACE FUNCTION postfix_virtual_alias_map(
    IN localpart varchar, IN the_domain varchar)
    RETURNS SETOF recipient_destination
AS $$
    DECLARE
        record recipient_destination;
        recipient varchar(320) := localpart || '@' || the_domain;
        did bigint := (SELECT gid FROM domain_name WHERE domainname=the_domain);
    BEGIN
        FOR record IN
            SELECT recipient, destination
              FROM alias
             WHERE gid = did
               AND address = localpart
            LOOP
                RETURN NEXT record;
            END LOOP;
        RETURN;
    END;
$$ LANGUAGE plpgsql STABLE
RETURNS NULL ON NULL INPUT
EXTERNAL SECURITY INVOKER;
-- ---
-- Parameters (from recipients address (MAIL TO) [localpart@the_domain]):
--      varchar localpart
--      varchar the_domain
-- Returns: address_maildir records
-- ---
CREATE OR REPLACE FUNCTION postfix_virtual_mailbox_map(
   IN localpart varchar, IN the_domain varchar) RETURNS SETOF address_maildir
AS $$
    DECLARE
        rec address_maildir;
        did bigint := (SELECT gid FROM domain_name WHERE domainname=the_domain);
        address varchar(320) := localpart || '@' || the_domain;
    BEGIN
        FOR rec IN
            SELECT address, domaindir||'/'||users.uid||'/'||directory||'/'
              FROM domain_data, users, maillocation
             WHERE domain_data.gid = did
               AND users.gid = did
               AND users.local_part = localpart
               AND maillocation.mid = users.mid
            LOOP
                RETURN NEXT rec;
            END LOOP;
        RETURN;
    END;
$$ LANGUAGE plpgsql STABLE
RETURNS NULL ON NULL INPUT
EXTERNAL SECURITY INVOKER;
-- ---
-- Parameters (from recipients address (MAIL TO) [localpart@the_domain]):
--      varchar localpart
--      varchar the_domain
-- Returns: recipient_uid records
-- ---
CREATE OR REPLACE FUNCTION postfix_virtual_uid_map(
    IN localpart varchar, IN the_domain varchar) RETURNS SETOF recipient_uid
AS $$
    DECLARE
        record recipient_uid;
        recipient varchar(320) := localpart || '@' || the_domain;
    BEGIN
        FOR record IN
            SELECT recipient, uid
              FROM users
             WHERE gid = (SELECT gid
                            FROM domain_name
                           WHERE domainname = the_domain)
               AND local_part = localpart
            LOOP
                RETURN NEXT record;
            END LOOP;
        RETURN;
    END;
$$ LANGUAGE plpgsql STABLE
RETURNS NULL ON NULL INPUT
EXTERNAL SECURITY INVOKER;
