-- ---
-- Clean out the old stuff
-- ---
DROP TYPE dovecotpassword CASCADE;

-- ---
-- Data type for function dovecotpassword(varchar, varchar)
-- ---
CREATE TYPE dovecotpassword AS (
    userid    varchar(320),
    password  varchar(74),
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

