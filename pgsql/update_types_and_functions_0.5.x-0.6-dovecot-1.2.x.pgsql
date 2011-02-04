SET client_encoding = 'UTF8';
SET client_min_messages = warning;


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


DROP TYPE dovecotpassword CASCADE;
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
