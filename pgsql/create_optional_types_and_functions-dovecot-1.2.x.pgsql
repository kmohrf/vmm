-- --- Information:
-- This file contains some data types and functions these should speed up some
-- operations. Read the comment on each data type/functions for more details.
-- ---

-- ---
-- Data type for function postfix_smtpd_sender_login_map(varchar, varchar)
-- ---
CREATE TYPE sender_login AS (
    sender  varchar(320),
    login   text
);

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

-- ########################################################################## --

-- ---
-- Data type for function postfix_virtual_mailbox(varchar, varchar)
-- ---
CREATE TYPE address_maildir AS (
    address varchar(320),
    maildir text
);

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

-- ########################################################################## --

-- ---
-- Data type for functions: postfix_relocated_map(varchar, varchar)
--                          postfix_virtual_alias_map(varchar, varchar)
-- ---
CREATE TYPE recipient_destination AS (
    recipient   varchar(320),
    destination text
);

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

-- ########################################################################## --

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

-- ########################################################################## --

-- ---
-- Data type for function postfix_transport_map(varchar, varchar)
-- ---
CREATE TYPE recipient_transport AS (
    recipient   varchar(320),
    transport   text
);

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

-- ########################################################################## --

-- ---
-- Data type for function postfix_virtual_uid_map(varchar, varchar)
-- ---
CREATE TYPE recipient_uid AS (
    recipient   varchar(320),
    uid         bigint
);

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

-- ########################################################################## --

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
-- Nearly the same as function dovecotuser above. It returns additionally the
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
               AND quotalimit.qid = users.qid
            LOOP
                RETURN NEXT record;
            END LOOP;
        RETURN;
    END;
$$ LANGUAGE plpgsql STABLE
RETURNS NULL ON NULL INPUT
EXTERNAL SECURITY INVOKER;

-- ########################################################################## --

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
-- Parameters (from login name [localpart@the_domain]):
--      varchar localpart
--      varchar the_domain
-- Returns: dovecotpassword records
--
-- Required access privileges for your dovecot database user:
--      GRANT SELECT ON users, domain_name TO dovecot;
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
