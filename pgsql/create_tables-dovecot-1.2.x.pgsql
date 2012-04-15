SET client_encoding = 'UTF8';
SET client_min_messages = warning;


CREATE SEQUENCE transport_id;

CREATE SEQUENCE mailboxformat_id;

CREATE SEQUENCE maillocation_id;

CREATE SEQUENCE quotalimit_id;

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
    sieve       boolean NOT NULL DEFAULT TRUE,
    CONSTRAINT  pkey_service_set PRIMARY KEY (ssid),
    CONSTRAINT  ukey_service_set UNIQUE (smtp, pop3, imap, sieve)
);
-- Insert all possible service combinations
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

CREATE TABLE domain_data (
    gid         bigint NOT NULL DEFAULT nextval('domain_gid'),
    qid         bigint NOT NULL DEFAULT 1, -- default quota limit
    ssid        bigint NOT NULL DEFAULT 1, -- default service set
    tid         bigint NOT NULL DEFAULT 1, -- default transport
    domaindir   varchar(40) NOT NULL, --/srv/mail/$RAND/4294967294
    note        text NULL DEFAULT NULL,
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
    qid         bigint NULL DEFAULT NULL,
    ssid        bigint NULL DEFAULT NULL,
    tid         bigint NULL DEFAULT NULL,
    note        text NULL DEFAULT NULL,
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

CREATE TABLE userquota (
    uid         bigint NOT NULL,
    bytes       bigint NOT NULL DEFAULT 0,
    messages    integer NOT NULL DEFAULT 0,
    CONSTRAINT  pkey_userquota PRIMARY KEY (uid),
    CONSTRAINT  fkey_userquota_uid_users FOREIGN KEY (uid)
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

CREATE TABLE catchall (
    gid         bigint NOT NULL,
    destination varchar(320) NOT NULL,
    CONSTRAINT  pkey_catchall PRIMARY KEY (gid, destination),
    CONSTRAINT  fkey_catchall_gid_domain_data FOREIGN KEY (gid)
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
               AND NOT domain_name.is_primary) AS aliasdomains,
           (SELECT count(gid)
              FROM catchall
             WHERE catchall.gid = domain_data.gid) AS catchall
      FROM domain_data
           LEFT JOIN domain_name USING (gid)
           LEFT JOIN users USING (gid)
     WHERE domain_name.is_primary
  GROUP BY gid;

-- ########################################################################## --

CREATE LANGUAGE plpgsql;

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
    userid    varchar(320),
    password  varchar(270),
    smtp      boolean,
    pop3      boolean,
    imap      boolean,
    sieve     boolean
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

-- ######################## TRIGGERs ######################################## --

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

-- ######################## FUNCTIONs ####################################### --

-- ---
-- Parameters (from login name [localpart@the_domain]):
--      varchar localpart
--      varchar the_domain
-- Returns: dovecotpassword records
--
-- Required access privileges for your dovecot database user:
--      GRANT SELECT ON users, domain_name, service_set TO dovecot;
--
-- For more details see http://wiki.dovecot.org/AuthDatabase/SQL
-- ---
CREATE OR REPLACE FUNCTION dovecotpassword(
    IN localpart varchar, IN the_domain varchar) RETURNS SETOF dovecotpassword
AS $$
    DECLARE
        record dovecotpassword;
        userid varchar(320) := localpart || '@' || the_domain;
    BEGIN
        FOR record IN
            SELECT userid, passwd, smtp, pop3, imap, sieve
              FROM users, service_set, domain_data
             WHERE users.gid = (SELECT gid
                                  FROM domain_name
                                 WHERE domainname = the_domain)
               AND local_part = localpart
               AND users.gid = domain_data.gid
               AND CASE WHEN
                     users.ssid IS NOT NULL
                     THEN
                       service_set.ssid = users.ssid
                     ELSE
                       service_set.ssid = domain_data.ssid
                     END
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
--
-- Required access privileges for your dovecot database user:
--      GRANT SELECT
--          ON users, domain_data, domain_name, maillocation, mailboxformat,
--             quotalimit
--          TO dovecot;
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
               AND CASE WHEN
                     users.qid IS NOT NULL
                   THEN
                     quotalimit.qid = users.qid
                   ELSE
                     quotalimit.qid = domain_data.qid
                   END
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
--
-- Required access privileges for your dovecot database user:
--      GRANT SELECT
--          ON users, domain_data, domain_name, maillocation, mailboxformat
--          TO dovecot;
--
-- For more details see http://wiki.dovecot.org/UserDatabase
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
--
-- Required access privileges for your postfix database user:
--      GRANT SELECT ON domain_name, relocated TO postfix;
--
-- For more details see postconf(5) section relocated_maps and relocated(5)
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
--
-- Required access privileges for your postfix database user:
--      GRANT SELECT ON domain_name, users, alias TO postfix;
--
-- For more details see postconf(5) section smtpd_sender_login_maps
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
--
-- Required access privileges for your postfix database user:
--      GRANT SELECT ON users, transport, domain_name TO postfix;
--
-- For more details see postconf(5) section transport_maps and transport(5)
-- ---
CREATE OR REPLACE FUNCTION postfix_transport_map(
    IN localpart varchar, IN the_domain varchar)
    RETURNS SETOF recipient_transport
AS $$
    DECLARE
        record recipient_transport;
        recipient varchar(320) := localpart || '@' || the_domain;
        did bigint := (SELECT gid FROM domain_name WHERE domainname = the_domain);
        transport_id bigint;
    BEGIN
        IF did IS NULL THEN
            RETURN;
        END IF;

        SELECT tid INTO transport_id
          FROM users
         WHERE gid = did AND local_part = localpart;

        IF transport_id IS NULL THEN
            SELECT tid INTO STRICT transport_id
              FROM domain_data
             WHERE gid = did;
        END IF;

        FOR record IN
            SELECT recipient, transport
              FROM transport
             WHERE tid = transport_id
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
--
-- Required access privileges for your postfix database user:
--      GRANT SELECT ON alias, domain_name TO postfix;
--
-- For more details see postconf(5) section virtual_alias_maps and virtual(5)
-- ---
CREATE OR REPLACE FUNCTION _interpolate_destination(
    IN destination varchar, localpart varchar, IN the_domain varchar)
    RETURNS varchar
AS $$
    DECLARE
        result varchar(320);
    BEGIN
        IF position('%' in destination) = 0 THEN
            RETURN destination;
        END IF;
        result := replace(destination, '%n', localpart);
        result := replace(result, '%d', the_domain);
        result := replace(result, '%=', localpart || '=' || the_domain);
        RETURN result;
    END;
$$ LANGUAGE plpgsql STABLE
RETURNS NULL ON NULL INPUT
EXTERNAL SECURITY INVOKER;

CREATE OR REPLACE FUNCTION postfix_virtual_alias_map(
    IN localpart varchar, IN the_domain varchar)
    RETURNS SETOF recipient_destination
AS $$
    DECLARE
        recordc recipient_destination;
        record recipient_destination;
        catchall_cursor refcursor;
        recipient varchar(320) := localpart || '@' || the_domain;
        did bigint := (SELECT gid FROM domain_name WHERE domainname=the_domain);
    BEGIN
        FOR record IN
            SELECT recipient,
                _interpolate_destination(destination, localpart, the_domain)
              FROM alias
             WHERE gid = did
               AND address = localpart
            LOOP
                RETURN NEXT record;
            END LOOP;

        IF NOT FOUND THEN
            -- There is no matching virtual_alias. If there are no catchall
            -- records for this domain, we can just return NULL since Postfix
            -- will then later consult mailboxes/relocated itself. But if
            -- there is a catchall destination, then it would take precedence
            -- over mailboxes/relocated, which is not what we want. Therefore,
            -- we must first find out if the query is for an existing mailbox
            -- or relocated entry and return the identity mapping if that is
            -- the case
            OPEN catchall_cursor FOR
                SELECT recipient,
                    _interpolate_destination(destination, localpart, the_domain)
                  FROM catchall
                 WHERE gid = did;
            FETCH NEXT FROM catchall_cursor INTO recordc;

            IF recordc IS NOT NULL THEN
                -- Since there are catchall records for this domain
                -- check the mailbox and relocated records and return identity
                -- if a matching record exists.
                FOR record IN
                    SELECT recipient, recipient as destination
                      FROM users
                    WHERE gid = did
                      AND local_part = localpart
                    UNION SELECT recipient, recipient as destination
                      FROM relocated
                    WHERE gid = did
                      AND address = localpart
                    LOOP
                        RETURN NEXT record;
                    END LOOP;

                IF NOT FOUND THEN
                    -- There were no records found for mailboxes/relocated,
                    -- so now we can actually iterate the cursor and populate
                    -- the return set
                    LOOP
                        RETURN NEXT recordc;
                        FETCH NEXT FROM catchall_cursor INTO recordc;
                        EXIT WHEN recordc IS NULL;
                    END LOOP;
                END IF;
            END IF;
            CLOSE catchall_cursor;
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
-- Returns: address_maildir records
--
-- Required access privileges for your postfix database user:
--      GRANT SELECT ON domain_data,domain_name,maillocation,users TO postfix;
--
-- For more details see postconf(5) section virtual_mailbox_maps
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
--
-- Required access privileges for your postfix database user:
--      GRANT SELECT ON users, domain_name TO postfix;
--
-- For more details see postconf(5) section virtual_uid_maps
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
